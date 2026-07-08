"""Tests for the UI module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from mesh_de_warper.core import Calibration
from mesh_de_warper.core.point import Point
from mesh_de_warper.core.profile import CalibrationProfile
from mesh_de_warper.interpolation import BilinearInterpolation
from mesh_de_warper.interpolation.rbf import RBFInterpolation
from mesh_de_warper.ui import CalibrationEditor, ProfileManager


class TestEditor:
    def test_instantiation(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        assert editor.get_calibration() is None

    def test_create_grid_defaults(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._create_grid()
        cal = editor.get_calibration()
        assert cal is not None
        assert cal.mesh.cols == 23
        assert cal.mesh.rows == 23

    def test_create_grid_custom_size(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._bed_width.setValue(100.0)
        editor._bed_height.setValue(50.0)
        editor._spacing.setValue(5.0)
        editor._create_grid()
        cal = editor.get_calibration()
        assert cal is not None
        assert cal.mesh.cols == 21
        assert cal.mesh.rows == 11

    def test_create_grid_rbf_multiquadric(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._interpolation.setCurrentIndex(3)
        editor._create_grid()
        assert editor.get_calibration() is not None

    def test_refresh_table_no_calibration(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._refresh_table()
        assert editor._table.rowCount() == 0

    def test_state_after_grid_creation(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        assert not editor._reset_btn.isEnabled()
        assert not editor._apply_btn.isEnabled()
        editor._create_grid()
        assert editor._reset_btn.isEnabled()
        assert editor._apply_btn.isEnabled()

    def test_apply_changes_no_calibration(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._apply_table_changes()

    def test_apply_changes_invalid_value(self, qtbot: object) -> None:
        with patch.object(QMessageBox, "warning") as mock_warn:
            editor = CalibrationEditor()
            editor._create_grid()
            editor._table.item(0, 2).setText("not_a_number")
            editor._apply_table_changes()
            mock_warn.assert_called_once()

    def test_apply_changes_valid_value(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._create_grid()
        editor._table.item(0, 2).setText("1.5")
        editor._apply_table_changes()
        assert editor._calibration.mesh[0, 0].offset_x == 1.5
        assert "Offsets updated" in editor._status.text()

    def test_reset_offsets_no_calibration(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._reset_offsets()

    def test_reset_offsets_yes(self, qtbot: object) -> None:
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            editor = CalibrationEditor()
            editor._create_grid()
            editor._calibration.mesh[0, 0] = Point(
                x=0, y=0, offset_x=1.0, offset_y=2.0
            )
            editor._reset_offsets()
            assert editor._calibration.mesh[0, 0].offset_x == 0.0
            assert "reset to zero" in editor._status.text()

    def test_reset_offsets_no(self, qtbot: object) -> None:
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            editor = CalibrationEditor()
            editor._create_grid()
            editor._calibration.mesh[0, 0] = Point(
                x=0, y=0, offset_x=1.0, offset_y=2.0
            )
            editor._reset_offsets()
            assert editor._calibration.mesh[0, 0].offset_x == 1.0

    def test_load_profile_cancel(self, qtbot: object) -> None:
        with patch.object(QFileDialog, "getOpenFileName", return_value=("", "")):
            editor = CalibrationEditor()
            editor._load_profile()
            assert editor.get_calibration() is None

    def test_load_profile_success(self, qtbot: object, temp_dir: Path) -> None:
        profile = CalibrationProfile(
            printer="Test", bed_width=200.0, bed_height=200.0,
            spacing=10.0, interpolation="bilinear",
            offsets={(0.0, 0.0): (1.0, 2.0)},
        )
        path = temp_dir / "test.json"
        profile.save(path)

        with patch.object(QFileDialog, "getOpenFileName",
                          return_value=(str(path), "")):
            editor = CalibrationEditor()
            editor._load_profile()
            assert editor.get_calibration() is not None
            assert "Loaded" in editor._status.text()

    def test_load_profile_unknown_interpolation(self, qtbot: object,
                                                temp_dir: Path) -> None:
        profile = CalibrationProfile(
            printer="Test", bed_width=200.0, bed_height=200.0,
            spacing=10.0, interpolation="nonexistent",
            offsets={(0.0, 0.0): (1.0, 2.0)},
        )
        path = temp_dir / "unknown.json"
        profile.save(path)

        with patch.object(QFileDialog, "getOpenFileName",
                          return_value=(str(path), "")):
            with patch.object(QMessageBox, "warning") as mock_warn:
                editor = CalibrationEditor()
                editor._load_profile()
                mock_warn.assert_called_once()
                assert editor.get_calibration() is not None

    def test_load_profile_rbf_multiquadric(self, qtbot: object,
                                           temp_dir: Path) -> None:
        profile = CalibrationProfile(
            printer="RBF", bed_width=200.0, bed_height=200.0,
            spacing=10.0, interpolation="rbf_multiquadric",
            offsets={(0.0, 0.0): (1.0, 2.0)},
        )
        path = temp_dir / "rbf.json"
        profile.save(path)
        with patch.object(QFileDialog, "getOpenFileName",
                          return_value=(str(path), "")):
            editor = CalibrationEditor()
            editor._load_profile()
            cal = editor.get_calibration()
            assert cal is not None
            assert "rbf" in cal.interpolation.name()

    def test_save_profile_no_calibration(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._save_profile()

    def test_save_profile_as_no_calibration(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        editor._save_profile_as()

    def test_save_profile_error(self, qtbot: object, temp_dir: Path) -> None:
        with patch.object(QMessageBox, "critical") as mock_crit:
            with patch.object(CalibrationProfile, "save",
                              side_effect=OSError("denied")):
                editor = CalibrationEditor()
                editor._create_grid()
                editor._path = temp_dir / "fail.json"
                editor._save_profile()
                mock_crit.assert_called_once()

    def test_load_profile_error(self, qtbot: object, temp_dir: Path) -> None:
        with patch.object(QFileDialog, "getOpenFileName",
                          return_value=(str(temp_dir / "nope.json"), "")):
            with patch.object(QMessageBox, "critical") as mock_crit:
                editor = CalibrationEditor()
                editor._load_profile()
                mock_crit.assert_called_once()

    def test_save_profile_with_path(self, qtbot: object, temp_dir: Path) -> None:
        editor = CalibrationEditor()
        editor._create_grid()
        editor._path = temp_dir / "auto.json"
        editor._save_profile()
        assert editor._path.exists()
        assert "Saved" in editor._status.text()

    def test_save_profile_without_path(self, qtbot: object, temp_dir: Path) -> None:
        with patch.object(QFileDialog, "getSaveFileName",
                          return_value=(str(temp_dir / "save_as.json"), "")):
            editor = CalibrationEditor()
            editor._create_grid()
            editor._save_profile()
            assert editor._path.exists()
            assert "Saved" in editor._status.text()

    def test_save_profile_as_cancel(self, qtbot: object) -> None:
        with patch.object(QFileDialog, "getSaveFileName", return_value=("", "")):
            editor = CalibrationEditor()
            editor._create_grid()
            editor._save_profile_as()

    def test_save_profile_as_success(self, qtbot: object, temp_dir: Path) -> None:
        with patch.object(QFileDialog, "getSaveFileName",
                          return_value=(str(temp_dir / "manual.json"), "")):
            editor = CalibrationEditor()
            editor._create_grid()
            editor._save_profile_as()
            assert editor._path == temp_dir / "manual.json"
            assert editor._path.exists()

    def test_save_profile_as_error(self, qtbot: object, temp_dir: Path) -> None:
        with patch.object(QFileDialog, "getSaveFileName",
                          return_value=(str(temp_dir / "bad.json"), "")):
            with patch.object(QMessageBox, "critical") as mock_crit:
                with patch.object(CalibrationProfile, "save",
                                  side_effect=OSError("denied")):
                    editor = CalibrationEditor()
                    editor._create_grid()
                    editor._save_profile_as()
                    mock_crit.assert_called_once()

    def test_load_calibration(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        cal = Calibration.for_bed(
            width=200.0, height=200.0, spacing=20.0,
            interpolation=BilinearInterpolation(),
        )
        editor.load_calibration(cal)
        assert editor.get_calibration() is not None
        assert editor._bed_width.value() == 200.0

    def test_load_calibration_unknown_interpolation(self, qtbot: object) -> None:
        editor = CalibrationEditor()
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=RBFInterpolation(kernel="gaussian"),
        )
        editor.load_calibration(cal)
        # Should fall back to index 0 when name not found
        assert editor._interpolation.currentIndex() == 0


class TestProfileManager:
    def test_instantiation(self, qtbot: object) -> None:
        pm = ProfileManager()
        assert pm.get_selected_profile() is None
        assert pm.get_selected_path() is None

    def test_load_from_file_cancel(self, qtbot: object) -> None:
        with patch.object(QFileDialog, "getOpenFileName", return_value=("", "")):
            pm = ProfileManager()
            pm._load_from_file()
            assert pm._list.count() == 0

    def test_load_from_file_success(self, qtbot: object, temp_dir: Path) -> None:
        profile = CalibrationProfile(
            printer="Test", bed_width=200.0, bed_height=200.0,
            spacing=10.0, interpolation="bilinear",
            offsets={(0.0, 0.0): (1.0, 2.0)},
        )
        path = temp_dir / "test.json"
        profile.save(path)

        with patch.object(QFileDialog, "getOpenFileName",
                          return_value=(str(path), "")):
            pm = ProfileManager()
            pm._load_from_file()
            assert pm._list.count() == 1
            assert pm._selected_profile is not None

    def test_load_from_file_error(self, qtbot: object, temp_dir: Path) -> None:
        with patch.object(QFileDialog, "getOpenFileName",
                          return_value=(str(temp_dir / "bad.json"), "")):
            with patch.object(QMessageBox, "critical") as mock_crit:
                pm = ProfileManager()
                pm._load_from_file()
                mock_crit.assert_called_once()

    def test_on_selection_changed_none(self, qtbot: object) -> None:
        pm = ProfileManager()
        pm._on_selection_changed()
        assert pm._selected_profile is None
        assert not pm._delete_btn.isEnabled()

    def test_on_selection_changed_with_path(self, qtbot: object,
                                            temp_dir: Path) -> None:
        profile = CalibrationProfile(
            printer="Test", bed_width=200.0, bed_height=200.0,
            spacing=10.0, interpolation="bilinear",
            offsets={(0.0, 0.0): (1.0, 2.0)},
        )
        path = temp_dir / "sel.json"
        profile.save(path)

        pm = ProfileManager()
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QListWidgetItem

        item = QListWidgetItem("Test")
        item.setData(Qt.UserRole, str(path))
        pm._list.addItem(item)
        pm._list.setCurrentItem(item)
        assert pm._selected_profile is not None
        assert pm._selected_path == path
        assert pm._delete_btn.isEnabled()

    def test_on_selection_changed_no_path_data(self, qtbot: object) -> None:
        from PyQt5.QtWidgets import QListWidgetItem
        pm = ProfileManager()
        item = QListWidgetItem("NoData")
        pm._list.addItem(item)
        pm._list.setCurrentItem(item)
        assert pm._selected_profile is None

    def test_on_selection_changed_bad_path(self, qtbot: object) -> None:
        pm = ProfileManager()
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QListWidgetItem

        item = QListWidgetItem("Bad")
        item.setData(Qt.UserRole, "/nonexistent/test.json")
        pm._list.addItem(item)
        pm._list.setCurrentItem(item)
        # Should handle gracefully without crashing
        assert pm._info.text() != ""

    def test_delete_selected_no(self, qtbot: object, temp_dir: Path) -> None:
        profile = CalibrationProfile(
            printer="Test", bed_width=200.0, bed_height=200.0,
            spacing=10.0, interpolation="bilinear",
            offsets={(0.0, 0.0): (1.0, 2.0)},
        )
        path = temp_dir / "del.json"
        profile.save(path)

        pm = ProfileManager()
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QListWidgetItem

        item = QListWidgetItem("Del")
        item.setData(Qt.UserRole, str(path))
        pm._list.addItem(item)
        pm._list.setCurrentItem(item)

        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            pm._delete_selected()
            assert path.exists()

    def test_delete_selected_yes(self, qtbot: object, temp_dir: Path) -> None:
        profile = CalibrationProfile(
            printer="Test", bed_width=200.0, bed_height=200.0,
            spacing=10.0, interpolation="bilinear",
            offsets={(0.0, 0.0): (1.0, 2.0)},
        )
        path = temp_dir / "del_yes.json"
        profile.save(path)

        pm = ProfileManager()
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QListWidgetItem

        item = QListWidgetItem("DelYes")
        item.setData(Qt.UserRole, str(path))
        pm._list.addItem(item)
        pm._list.setCurrentItem(item)

        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            pm._delete_selected()
            assert not path.exists()
            assert pm._list.count() == 0

    def test_delete_selected_error(self, qtbot: object, temp_dir: Path) -> None:
        profile = CalibrationProfile(
            printer="Test", bed_width=200.0, bed_height=200.0,
            spacing=10.0, interpolation="bilinear",
            offsets={(0.0, 0.0): (1.0, 2.0)},
        )
        path = temp_dir / "del_err.json"
        profile.save(path)

        pm = ProfileManager()
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QListWidgetItem

        item = QListWidgetItem("DelErr")
        item.setData(Qt.UserRole, str(path))
        pm._list.addItem(item)
        pm._list.setCurrentItem(item)

        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            with patch.object(Path, "unlink",
                              side_effect=OSError("permission denied")):
                with patch.object(QMessageBox, "critical") as mock_crit:
                    pm._delete_selected()
                    mock_crit.assert_called_once()

    def test_delete_selected_no_item(self, qtbot: object) -> None:
        pm = ProfileManager()
        pm._delete_selected()  # Should not crash
