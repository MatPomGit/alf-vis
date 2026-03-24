"""Tests for image_analysis.object_classes module."""

from __future__ import annotations

import pytest

from image_analysis.detection import Detection
from image_analysis.object_classes import (
    YOLO_LABEL_TO_CLASS,
    ObjectClass,
    classify_detection,
    classify_detections,
    filter_by_class,
)


@pytest.fixture
def sample_detections() -> list[Detection]:
    return [
        Detection(label="person", confidence=0.9, bbox=(0, 0, 50, 100)),
        Detection(label="chair", confidence=0.8, bbox=(60, 0, 120, 100)),
        Detection(label="dining table", confidence=0.7, bbox=(130, 0, 250, 100)),
        Detection(label="banana", confidence=0.6, bbox=(260, 0, 310, 100)),
    ]


class TestObjectClass:
    def test_all_required_classes_exist(self) -> None:
        for cls in (
            ObjectClass.CHAIR,
            ObjectClass.TABLE,
            ObjectClass.CARTON,
            ObjectClass.PERSON,
            ObjectClass.WALL,
            ObjectClass.UNKNOWN,
        ):
            assert isinstance(cls, ObjectClass)


class TestYoloLabelToClass:
    def test_person_maps_to_person(self) -> None:
        assert YOLO_LABEL_TO_CLASS["person"] is ObjectClass.PERSON

    def test_chair_maps_to_chair(self) -> None:
        assert YOLO_LABEL_TO_CLASS["chair"] is ObjectClass.CHAIR

    def test_dining_table_maps_to_table(self) -> None:
        assert YOLO_LABEL_TO_CLASS["dining table"] is ObjectClass.TABLE


class TestClassifyDetection:
    def test_person_label(self) -> None:
        det = Detection(label="person", confidence=0.9, bbox=(0, 0, 50, 50))
        assert classify_detection(det) is ObjectClass.PERSON

    def test_chair_label(self) -> None:
        det = Detection(label="chair", confidence=0.8, bbox=(0, 0, 50, 50))
        assert classify_detection(det) is ObjectClass.CHAIR

    def test_unknown_label_returns_unknown(self) -> None:
        det = Detection(label="elephant", confidence=0.7, bbox=(0, 0, 50, 50))
        assert classify_detection(det) is ObjectClass.UNKNOWN

    def test_case_insensitive(self) -> None:
        det = Detection(label="PERSON", confidence=0.9, bbox=(0, 0, 50, 50))
        assert classify_detection(det) is ObjectClass.PERSON


class TestClassifyDetections:
    def test_returns_same_length(
        self, sample_detections: list[Detection]
    ) -> None:
        result = classify_detections(sample_detections)
        assert len(result) == len(sample_detections)

    def test_pairs_are_detection_and_class(
        self, sample_detections: list[Detection]
    ) -> None:
        for det, cls in classify_detections(sample_detections):
            assert isinstance(det, Detection)
            assert isinstance(cls, ObjectClass)

    def test_empty_input_returns_empty(self) -> None:
        assert classify_detections([]) == []


class TestFilterByClass:
    def test_filters_to_persons(
        self, sample_detections: list[Detection]
    ) -> None:
        persons = filter_by_class(sample_detections, ObjectClass.PERSON)
        assert len(persons) == 1
        assert persons[0].label == "person"

    def test_unknown_class_returns_banana(
        self, sample_detections: list[Detection]
    ) -> None:
        unknowns = filter_by_class(sample_detections, ObjectClass.UNKNOWN)
        assert len(unknowns) == 1
        assert unknowns[0].label == "banana"

    def test_empty_input_returns_empty(self) -> None:
        assert filter_by_class([], ObjectClass.PERSON) == []
