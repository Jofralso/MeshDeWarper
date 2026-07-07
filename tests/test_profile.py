"""Tests for CalibrationProfile serialisation."""

from __future__ import annotations

import json
from pathlib import Path

from cura_xy_calibration.core.profile import CalibrationProfile


class TestCalibrationProfile:
    def test_default_creation(self) -> None:
        p = CalibrationProfile()
        assert p.printer == ""
        assert p.bed_width == 220.0
        assert p.bed_height == 220.0
        assert p.spacing == 10.0
        assert p.interpolation == "bilinear"
        assert p.version == 1
        assert p.created_at != ""

    def test_to_dict(self, sample_profile: CalibrationProfile) -> None:
        d = sample_profile.to_dict()
        assert d["printer"] == "TestPrinter"
        assert d["bed_width"] == 220.0
        assert d["version"] == 1
        assert len(d["offsets"]) == 4
        assert d["offsets"][0]["x"] == 0.0
        assert d["offsets"][0]["offset_x"] == 0.1

    def test_from_dict(self, sample_profile: CalibrationProfile) -> None:
        d = sample_profile.to_dict()
        restored = CalibrationProfile.from_dict(d)
        assert restored.printer == sample_profile.printer
        assert restored.bed_width == sample_profile.bed_width
        assert restored.offsets[(0.0, 0.0)] == (0.1, 0.2)

    def test_save_and_load(self, sample_profile: CalibrationProfile, temp_dir: Path) -> None:
        path = temp_dir / "test_profile.json"
        sample_profile.save(path)
        assert path.exists()

        loaded = CalibrationProfile.load(path)
        assert loaded.printer == sample_profile.printer
        assert loaded.bed_width == sample_profile.bed_width
        assert loaded.offsets == sample_profile.offsets

    def test_round_trip_json(self, sample_profile: CalibrationProfile) -> None:
        d = sample_profile.to_dict()
        json_str = json.dumps(d)
        restored_d = json.loads(json_str)
        restored = CalibrationProfile.from_dict(restored_d)
        assert restored.printer == "TestPrinter"
        assert (0.0, 0.0) in restored.offsets

    def test_empty_offsets(self) -> None:
        p = CalibrationProfile(offsets={})
        d = p.to_dict()
        assert d["offsets"] == []
        restored = CalibrationProfile.from_dict(d)
        assert restored.offsets == {}

    def test_metadata(self) -> None:
        p = CalibrationProfile(metadata={"source": "vision", "confidence": 0.85})
        d = p.to_dict()
        assert d["metadata"]["source"] == "vision"
        restored = CalibrationProfile.from_dict(d)
        assert restored.metadata["confidence"] == 0.85

    def test_extension_added(self, sample_profile: CalibrationProfile, temp_dir: Path) -> None:
        path = temp_dir / "profile"  # no extension
        sample_profile.save(path)
        assert (temp_dir / "profile.json").exists()

    def test_serialise_deserialise_preserves_version(
        self, sample_profile: CalibrationProfile
    ) -> None:  # noqa: E501
        d = sample_profile.to_dict()
        restored = CalibrationProfile.from_dict(d)
        assert restored.version == sample_profile.version
