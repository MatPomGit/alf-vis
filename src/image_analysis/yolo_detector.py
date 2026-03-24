"""YOLO-based object detection using the Ultralytics framework.

Wraps the Ultralytics ``YOLO`` class (YOLOv8 / YOLOv10 / YOLOv11) to provide
a consistent API for object detection on images from the Unitree G1 EDU robot.

Implementation notes:
    - Requires ``ultralytics>=8.0``:  ``pip install ultralytics``
    - Pre-trained weights are stored in the ``models/`` directory.
    - GPU inference is used automatically when a CUDA device is available.
    - For real-time operation, the ``yolov8n.pt`` (nano) or ``yolov8s.pt``
      (small) variant is recommended on the robot's onboard CPU.
    - Custom fine-tuned weights can be supplied via :attr:`YoloConfig.weights`.
    - The detector is intentionally kept separate from :mod:`detection` so that
      the base module has no heavy ML dependency.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from image_analysis.detection import Detection

logger = logging.getLogger(__name__)

# Default detection confidence for YOLO inference.
YOLO_DEFAULT_CONFIDENCE: float = 0.45

# Default IoU threshold for YOLO-internal NMS.
YOLO_DEFAULT_IOU: float = 0.45

# Maximum number of detections returned per image.
YOLO_MAX_DETECTIONS: int = 300


@dataclass
class YoloConfig:
    """Configuration for the YOLO detector.

    Attributes:
        weights: Path to the model weights file (``.pt``) or a model name
            that Ultralytics will download automatically, e.g.
            ``"yolov8n.pt"``.
        confidence: Minimum confidence threshold for returning a detection.
        iou: IoU threshold for built-in Non-Maximum Suppression.
        device: Inference device string accepted by PyTorch, e.g.
            ``"cpu"``, ``"cuda:0"``, ``"mps"``.
        max_detections: Maximum number of boxes to return per inference call.
        image_size: Inference image size in pixels (square).  Common values:
            320, 416, 640 (default).
    """

    weights: str | Path = "yolov8n.pt"
    confidence: float = YOLO_DEFAULT_CONFIDENCE
    iou: float = YOLO_DEFAULT_IOU
    device: str = "cpu"
    max_detections: int = YOLO_MAX_DETECTIONS
    image_size: int = 640


class YoloDetector:
    """High-level YOLO object detector.

    Loads an Ultralytics YOLO model and exposes a simple inference interface
    that returns :class:`~image_analysis.detection.Detection` objects
    compatible with the rest of the ``image_analysis`` pipeline.

    Example::

        config = YoloConfig(weights="yolov8n.pt", device="cpu")
        detector = YoloDetector(config)
        detections = detector.detect(frame)

    Args:
        config: YOLO configuration parameters.

    Raises:
        ImportError: If ``ultralytics`` is not installed.
    """

    def __init__(self, config: YoloConfig | None = None) -> None:
        self._config = config or YoloConfig()
        self._model: object | None = None

    def load(self) -> None:
        """Load the YOLO model into memory.

        Downloads pre-trained weights from the Ultralytics CDN when *weights*
        is a bare model name (e.g. ``"yolov8n.pt"``).

        Raises:
            ImportError: If the ``ultralytics`` package is not installed.
            FileNotFoundError: If a custom weights path does not exist.
        """
        try:
            from ultralytics import YOLO  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "YOLO detection requires 'ultralytics'. "
                "Install it with: pip install ultralytics"
            ) from exc

        weights = self._config.weights
        if isinstance(weights, Path) and not weights.is_file():
            raise FileNotFoundError(f"YOLO weights file not found: {weights}")

        self._model = YOLO(str(weights))
        logger.info("YOLO model loaded from '%s'.", weights)

    @property
    def is_loaded(self) -> bool:
        """Return ``True`` if the model has been loaded."""
        return self._model is not None

    def detect(
        self,
        image: np.ndarray,
        confidence: float | None = None,
        iou: float | None = None,
    ) -> list[Detection]:
        """Run YOLO inference on *image* and return detections.

        Args:
            image: BGR ``uint8`` image array with shape ``(H, W, 3)``.
            confidence: Override the configured confidence threshold.
            iou: Override the configured IoU threshold.

        Returns:
            List of :class:`~image_analysis.detection.Detection` objects
            sorted by descending confidence.

        Raises:
            RuntimeError: If :meth:`load` has not been called first.
            TypeError: If *image* is not a ``np.ndarray``.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
        if not self.is_loaded or self._model is None:
            raise RuntimeError(
                "YOLO model is not loaded. Call YoloDetector.load() first."
            )

        conf = confidence if confidence is not None else self._config.confidence
        nms_iou = iou if iou is not None else self._config.iou

        results = self._model(  # type: ignore[operator]
            image,
            conf=conf,
            iou=nms_iou,
            device=self._config.device,
            imgsz=self._config.image_size,
            max_det=self._config.max_detections,
            verbose=False,
        )

        detections = _parse_ultralytics_results(results)
        detections.sort(key=lambda d: d.confidence, reverse=True)
        logger.debug("YOLO detected %d objects.", len(detections))
        return detections


def _parse_ultralytics_results(results: list[object]) -> list[Detection]:
    """Convert Ultralytics result objects to :class:`Detection` instances.

    Args:
        results: List of ``ultralytics.engine.results.Results`` objects
            returned by a YOLO forward pass.

    Returns:
        Flat list of :class:`Detection` objects.
    """
    detections: list[Detection] = []
    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        names: dict[int, str] = getattr(result, "names", {})
        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = names.get(cls_id, str(cls_id))
            bbox = (int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
            detections.append(
                Detection(label=label, confidence=conf, bbox=bbox)
            )
    return detections


def load_yolo_model(
    weights: str | Path = "yolov8n.pt",
    device: str = "cpu",
) -> YoloDetector:
    """Convenience factory - create and load a :class:`YoloDetector`.

    Args:
        weights: Path or name of the YOLO weights file.
        device: Inference device (``"cpu"``, ``"cuda:0"``, etc.).

    Returns:
        A loaded :class:`YoloDetector` ready for inference.

    Raises:
        ImportError: If ``ultralytics`` is not installed.
    """
    detector = YoloDetector(YoloConfig(weights=weights, device=device))
    detector.load()
    return detector
