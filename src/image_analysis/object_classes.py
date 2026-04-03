"""Object class definitions and YOLO-to-domain-class mapping.

Maps YOLO COCO class labels to the five object categories relevant to the
Unitree G1 EDU navigation task:

- **CHAIR** - sitting furniture
- **TABLE** - flat horizontal surfaces used as work surfaces
- **CARTON** - cardboard boxes and packages
- **PERSON** - humans in the scene
- **WALL** - vertical flat surfaces (walls, doors, large panels)

Any COCO label not covered by the mapping is classified as :attr:`ObjectClass.UNKNOWN`.

Implementation notes:
    - The mapping :data:`YOLO_LABEL_TO_CLASS` covers the 80 COCO classes.
    - For custom fine-tuned weights, update :data:`YOLO_LABEL_TO_CLASS` to
      match the model's class names.
    - Additional classes can be added by extending the :class:`ObjectClass`
      enum and the mapping dictionary.
"""

from __future__ import annotations

import logging
from enum import Enum, auto

from image_analysis.detection import Detection

logger = logging.getLogger(__name__)


class ObjectClass(Enum):
    """Domain-specific object classes for Unitree G1 EDU navigation.

    Attributes:
        CHAIR: A chair or similar seating object.
        TABLE: A table, desk, or similar horizontal surface.
        CARTON: A cardboard box or package.
        PERSON: A human.
        WALL: A wall, large panel, or door.
        UNKNOWN: Any object not covered by the defined classes.
    """

    CHAIR = auto()
    TABLE = auto()
    CARTON = auto()
    PERSON = auto()
    WALL = auto()
    UNKNOWN = auto()


# ---------------------------------------------------------------------------
# YOLO COCO label → ObjectClass mapping
# ---------------------------------------------------------------------------

#: Maps YOLO/COCO class labels (lowercase strings) to :class:`ObjectClass`.
#: Extend this dictionary when using custom fine-tuned model weights.
YOLO_LABEL_TO_CLASS: dict[str, ObjectClass] = {
    # Persons
    "person": ObjectClass.PERSON,
    # Furniture - chairs
    "chair": ObjectClass.CHAIR,
    # Furniture - tables / desks
    "dining table": ObjectClass.TABLE,
    "table": ObjectClass.TABLE,
    "desk": ObjectClass.TABLE,
    # Boxes / cartons
    "suitcase": ObjectClass.CARTON,
    "backpack": ObjectClass.CARTON,
    "handbag": ObjectClass.CARTON,
    "box": ObjectClass.CARTON,
    "carton": ObjectClass.CARTON,
}


def classify_detection(detection: Detection) -> ObjectClass:
    """Map a single YOLO detection to a domain :class:`ObjectClass`.

    Performs a case-insensitive lookup of the detection label in
    :data:`YOLO_LABEL_TO_CLASS`.

    Args:
        detection: A :class:`~image_analysis.detection.Detection` from YOLO
            or any detector that returns a *label* string.

    Returns:
        The matching :class:`ObjectClass`, or :attr:`ObjectClass.UNKNOWN`
        when the label has no mapping.
    """
    obj_class = YOLO_LABEL_TO_CLASS.get(detection.label.lower(), ObjectClass.UNKNOWN)
    if obj_class is ObjectClass.UNKNOWN:
        logger.debug("No class mapping for label '%s'; assigning UNKNOWN.", detection.label)
    return obj_class


def classify_detections(detections: list[Detection]) -> list[tuple[Detection, ObjectClass]]:
    """Map a list of detections to domain classes.

    Args:
        detections: List of :class:`~image_analysis.detection.Detection` objects.

    Returns:
        List of ``(detection, object_class)`` pairs in the same order as
        *detections*.
    """
    return [(det, classify_detection(det)) for det in detections]


def filter_by_class(
    detections: list[Detection],
    target_class: ObjectClass,
) -> list[Detection]:
    """Return only detections that map to *target_class*.

    Args:
        detections: List of detections to filter.
        target_class: The :class:`ObjectClass` to keep.

    Returns:
        Sub-list of *detections* that map to *target_class*.
    """
    return [d for d in detections if classify_detection(d) is target_class]
