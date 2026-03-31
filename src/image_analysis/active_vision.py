"""Active vision module for adaptive image-region optimisation.

The module implements a lightweight active-vision strategy that dynamically
selects the most informative Region of Interest (ROI) for downstream analysis.
It combines three cues:

1. **Task relevance** from detector confidence and object size.
2. **Novelty / exploration** favouring regions that differ from the previous ROI.
3. **Stability** to avoid jittering attention between distant regions.

The optimiser can be used in real-time loops where each frame provides a set of
object detections and (optionally) a per-pixel uncertainty map.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from image_analysis.detection import Detection


@dataclass(frozen=True)
class RegionOfInterest:
    """Rectangular region of interest in image pixel coordinates.

    Attributes:
        x1: Left edge (inclusive).
        y1: Top edge (inclusive).
        x2: Right edge (exclusive).
        y2: Bottom edge (exclusive).
    """

    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) * 0.5, (self.y1 + self.y2) * 0.5)


@dataclass(frozen=True)
class ActiveVisionConfig:
    """Configuration of the active-vision optimisation policy."""

    roi_scale: float = 1.6
    min_roi_ratio: float = 0.2
    max_roi_ratio: float = 0.8
    exploration_weight: float = 0.25
    stability_weight: float = 0.20
    uncertainty_weight: float = 0.30


class ActiveVisionOptimizer:
    """Select the most informative image area using active-vision heuristics."""

    def __init__(self, config: ActiveVisionConfig | None = None) -> None:
        self.config = config or ActiveVisionConfig()

    def optimize_region(
        self,
        image_shape: tuple[int, int] | tuple[int, int, int],
        detections: list[Detection],
        previous_roi: RegionOfInterest | None = None,
        uncertainty_map: np.ndarray | None = None,
    ) -> RegionOfInterest:
        """Return an ROI optimised for the next processing step.

        Args:
            image_shape: Image shape as ``(H, W)`` or ``(H, W, C)``.
            detections: Detected objects in the current frame.
            previous_roi: Previously selected ROI for temporal consistency.
            uncertainty_map: Optional uncertainty map in range ``[0, 1]``.

        Returns:
            Selected ROI clipped to image boundaries.
        """
        height, width = self._parse_image_shape(image_shape)
        if not detections:
            return self._default_roi(width=width, height=height)

        candidates = [self._candidate_from_detection(det, width, height) for det in detections]

        best_candidate = max(
            candidates,
            key=lambda roi: self._score_roi(
                roi=roi,
                detections=detections,
                previous_roi=previous_roi,
                uncertainty_map=uncertainty_map,
                width=width,
                height=height,
            ),
        )
        return best_candidate

    def _score_roi(
        self,
        roi: RegionOfInterest,
        detections: list[Detection],
        previous_roi: RegionOfInterest | None,
        uncertainty_map: np.ndarray | None,
        width: int,
        height: int,
    ) -> float:
        relevance = self._relevance_score(roi, detections)
        exploration = self._exploration_score(roi, width=width, height=height)
        stability = self._stability_score(roi, previous_roi)
        uncertainty = self._uncertainty_score(roi, uncertainty_map)

        return (
            relevance
            + self.config.exploration_weight * exploration
            + self.config.stability_weight * stability
            + self.config.uncertainty_weight * uncertainty
        )

    def _relevance_score(self, roi: RegionOfInterest, detections: list[Detection]) -> float:
        score = 0.0
        for det in detections:
            det_roi = RegionOfInterest(*det.bbox)
            overlap = self._iou(roi, det_roi)
            if overlap <= 0.0:
                continue
            score += float(det.confidence) * overlap
        return score

    def _exploration_score(self, roi: RegionOfInterest, width: int, height: int) -> float:
        cx, cy = roi.center
        dx = abs(cx - (width * 0.5)) / max(width * 0.5, 1.0)
        dy = abs(cy - (height * 0.5)) / max(height * 0.5, 1.0)
        # Prefer non-central areas slightly to encourage exploration.
        return min(1.0, np.hypot(dx, dy))

    def _stability_score(
        self, roi: RegionOfInterest, previous_roi: RegionOfInterest | None
    ) -> float:
        if previous_roi is None:
            return 0.0
        cx, cy = roi.center
        px, py = previous_roi.center
        distance = np.hypot(cx - px, cy - py)
        normaliser = max(np.hypot(previous_roi.width, previous_roi.height), 1.0)
        return 1.0 - min(1.0, distance / normaliser)

    def _uncertainty_score(self, roi: RegionOfInterest, uncertainty_map: np.ndarray | None) -> float:
        if uncertainty_map is None:
            return 0.0
        if uncertainty_map.ndim != 2:
            raise ValueError(
                f"uncertainty_map must be 2-D, got shape {uncertainty_map.shape}"
            )
        region = uncertainty_map[roi.y1 : roi.y2, roi.x1 : roi.x2]
        if region.size == 0:
            return 0.0
        return float(np.clip(region.mean(), 0.0, 1.0))

    def _candidate_from_detection(self, det: Detection, width: int, height: int) -> RegionOfInterest:
        x1, y1, x2, y2 = det.bbox
        box_w = max(1, x2 - x1)
        box_h = max(1, y2 - y1)
        scaled_w = int(box_w * self.config.roi_scale)
        scaled_h = int(box_h * self.config.roi_scale)

        min_side = int(min(width, height) * self.config.min_roi_ratio)
        max_side = int(min(width, height) * self.config.max_roi_ratio)
        side = max(min_side, min(max_side, max(scaled_w, scaled_h)))

        cx = int((x1 + x2) * 0.5)
        cy = int((y1 + y2) * 0.5)

        return self._clip_roi(
            RegionOfInterest(
                x1=cx - side // 2,
                y1=cy - side // 2,
                x2=cx + side // 2,
                y2=cy + side // 2,
            ),
            width=width,
            height=height,
        )

    @staticmethod
    def _clip_roi(roi: RegionOfInterest, width: int, height: int) -> RegionOfInterest:
        x1 = max(0, min(width - 1, roi.x1))
        y1 = max(0, min(height - 1, roi.y1))
        x2 = max(x1 + 1, min(width, roi.x2))
        y2 = max(y1 + 1, min(height, roi.y2))
        return RegionOfInterest(x1=x1, y1=y1, x2=x2, y2=y2)

    def _default_roi(self, width: int, height: int) -> RegionOfInterest:
        side = int(min(width, height) * self.config.min_roi_ratio)
        side = max(1, side)
        cx = width // 2
        cy = height // 2
        return self._clip_roi(
            RegionOfInterest(
                x1=cx - side // 2,
                y1=cy - side // 2,
                x2=cx + side // 2,
                y2=cy + side // 2,
            ),
            width=width,
            height=height,
        )

    @staticmethod
    def _parse_image_shape(shape: tuple[int, ...]) -> tuple[int, int]:
        if len(shape) < 2:
            raise ValueError(f"image_shape must have at least 2 dimensions, got {shape}")
        height, width = shape[0], shape[1]
        if height <= 0 or width <= 0:
            raise ValueError(f"image_shape must be positive, got {shape}")
        return int(height), int(width)

    @staticmethod
    def _iou(a: RegionOfInterest, b: RegionOfInterest) -> float:
        inter_x1 = max(a.x1, b.x1)
        inter_y1 = max(a.y1, b.y1)
        inter_x2 = min(a.x2, b.x2)
        inter_y2 = min(a.y2, b.y2)
        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        union = a.area + b.area - inter_area
        if union <= 0:
            return 0.0
        return float(inter_area) / float(union)
