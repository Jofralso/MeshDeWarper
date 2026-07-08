"""Interactive calibration editor widget."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mesh_de_warper.core import Calibration, Point
from mesh_de_warper.interpolation import (
    BilinearInterpolation,
    InterpolationAlgorithm,
)

logger = logging.getLogger(__name__)

INTERPOLATION_ALGOS: dict[str, type[InterpolationAlgorithm]] = {
    "bilinear": BilinearInterpolation,
}

try:
    from mesh_de_warper.interpolation.bicubic import BicubicInterpolation

    INTERPOLATION_ALGOS["bicubic"] = BicubicInterpolation
except ImportError:  # pragma: no cover
    pass  # pragma: no cover

try:
    from mesh_de_warper.interpolation.tps import ThinPlateSplineInterpolation

    INTERPOLATION_ALGOS["thin_plate_spline"] = ThinPlateSplineInterpolation
except ImportError:  # pragma: no cover
    pass  # pragma: no cover

try:
    from mesh_de_warper.interpolation.rbf import RBFInterpolation

    INTERPOLATION_ALGOS["rbf_multiquadric"] = RBFInterpolation
except ImportError:  # pragma: no cover
    pass  # pragma: no cover

DECIMAL = 3


class CalibrationEditor(QWidget):
    """Main interactive editor for XY distortion calibration.

    Provides a table-based point editor, grid configuration,
    interpolation selection, and profile management.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._calibration: Calibration | None = None
        self._path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # --- Grid configuration ---
        config_group = QGroupBox("Grid Configuration")
        config_layout = QFormLayout(config_group)

        hbox = QHBoxLayout()
        self._bed_width = QDoubleSpinBox()
        self._bed_width.setRange(1, 1000)
        self._bed_width.setValue(220)
        self._bed_width.setSuffix(" mm")
        hbox.addWidget(self._bed_width)
        self._bed_height = QDoubleSpinBox()
        self._bed_height.setRange(1, 1000)
        self._bed_height.setValue(220)
        self._bed_height.setSuffix(" mm")
        hbox.addWidget(self._bed_height)
        config_layout.addRow("Bed size:", hbox)

        self._spacing = QDoubleSpinBox()
        self._spacing.setRange(0.5, 100)
        self._spacing.setValue(10)
        self._spacing.setSuffix(" mm")
        self._spacing.setDecimals(2)
        config_layout.addRow("Spacing:", self._spacing)

        self._interpolation = QComboBox()
        for name in INTERPOLATION_ALGOS:
            self._interpolation.addItem(name)
        config_layout.addRow("Interpolation:", self._interpolation)

        btn_row = QHBoxLayout()
        self._create_btn = QPushButton("Create Grid")
        self._create_btn.clicked.connect(self._create_grid)
        btn_row.addWidget(self._create_btn)

        self._reset_btn = QPushButton("Reset Offsets")
        self._reset_btn.clicked.connect(self._reset_offsets)
        self._reset_btn.setEnabled(False)
        btn_row.addWidget(self._reset_btn)

        config_layout.addRow(btn_row)
        layout.addWidget(config_group)

        # --- Point table ---
        table_group = QGroupBox("Calibration Points")
        table_layout = QVBoxLayout(table_group)

        self._table = QTableWidget()
        self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectItems)
        table_layout.addWidget(self._table)

        table_btn_row = QHBoxLayout()
        self._apply_btn = QPushButton("Apply Changes")
        self._apply_btn.clicked.connect(self._apply_table_changes)
        self._apply_btn.setEnabled(False)
        table_btn_row.addWidget(self._apply_btn)
        table_btn_row.addStretch()
        table_layout.addLayout(table_btn_row)

        layout.addWidget(table_group)

        # --- Profile management ---
        profile_group = QGroupBox("Profile")
        profile_layout = QHBoxLayout(profile_group)

        self._load_btn = QPushButton("Load")
        self._load_btn.clicked.connect(self._load_profile)
        profile_layout.addWidget(self._load_btn)

        self._save_btn = QPushButton("Save")
        self._save_btn.clicked.connect(self._save_profile)
        self._save_btn.setEnabled(False)
        profile_layout.addWidget(self._save_btn)

        self._save_as_btn = QPushButton("Save As...")
        self._save_as_btn.clicked.connect(self._save_profile_as)
        self._save_as_btn.setEnabled(False)
        profile_layout.addWidget(self._save_as_btn)

        layout.addWidget(profile_group)

        # --- Status ---
        self._status = QLabel("No calibration loaded.")
        layout.addWidget(self._status)

    # --- Grid creation ---

    def _create_grid(self) -> None:
        width = self._bed_width.value()
        height = self._bed_height.value()
        spacing = self._spacing.value()
        algo_name = self._interpolation.currentText()
        algo_cls = INTERPOLATION_ALGOS[algo_name]

        if algo_name == "rbf_multiquadric":
            interpolation = algo_cls(kernel="multiquadric")  # type: ignore[call-arg]
        else:
            interpolation = algo_cls()

        self._calibration = Calibration.for_bed(
            width=width,
            height=height,
            spacing=spacing,
            interpolation=interpolation,
        )
        self._path = None
        self._refresh_table()
        self._update_state()
        self._status.setText(
            f"Grid created: {self._calibration.mesh.cols}x{self._calibration.mesh.rows} "
            f"({self._calibration.mesh.num_points} points)"
        )

    # --- Table management ---

    def _refresh_table(self) -> None:
        if self._calibration is None:
            return
        mesh = self._calibration.mesh
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Row", "Col", "Offset X (mm)", "Offset Y (mm)"])
        self._table.setRowCount(mesh.num_points)

        for idx, (row, col, point) in enumerate(mesh.iter_with_index()):
            self._table.setItem(idx, 0, QTableWidgetItem(str(row)))
            self._table.setItem(idx, 1, QTableWidgetItem(str(col)))
            item_x = QTableWidgetItem(f"{point.offset_x:.{DECIMAL}f}")
            item_x.setData(Qt.UserRole, point.offset_x)
            self._table.setItem(idx, 2, item_x)
            item_y = QTableWidgetItem(f"{point.offset_y:.{DECIMAL}f}")
            item_y.setData(Qt.UserRole, point.offset_y)
            self._table.setItem(idx, 3, item_y)

    def _apply_table_changes(self) -> None:
        if self._calibration is None:
            return
        mesh = self._calibration.mesh
        errors = 0
        for idx, (row, col, point) in enumerate(mesh.iter_with_index()):
            try:
                ox = float(self._table.item(idx, 2).text())
                oy = float(self._table.item(idx, 3).text())
                mesh[row, col] = Point(x=point.x, y=point.y, offset_x=ox, offset_y=oy)
            except (ValueError, AttributeError):
                errors += 1

        if errors:
            QMessageBox.warning(self, "Input Error", f"{errors} row(s) had invalid values.")
        else:
            self._status.setText(f"Offsets updated ({mesh.num_points} points).")
        self._refresh_table()

    def _reset_offsets(self) -> None:
        if self._calibration is None:
            return
        reply = QMessageBox.question(
            self, "Reset Offsets", "Reset all calibration offsets to zero?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._calibration.mesh.reset_offsets()
            self._refresh_table()
            self._status.setText("All offsets reset to zero.")

    # --- Profile management ---

    def _load_profile(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Load Calibration Profile", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            from mesh_de_warper.core.profile import CalibrationProfile

            profile = CalibrationProfile.load(path)
            algo_name = profile.interpolation
            algo_cls = INTERPOLATION_ALGOS.get(algo_name)
            if algo_cls is None:
                QMessageBox.warning(
                    self, "Unknown Interpolation",
                    f"Interpolation '{algo_name}' not available. Using bilinear.",
                )
                algo_cls = BilinearInterpolation

            if algo_name == "rbf_multiquadric":
                interpolation = algo_cls(kernel="multiquadric")  # type: ignore[call-arg]
            else:
                interpolation = algo_cls()

            self._calibration = Calibration.from_profile(profile, interpolation)
            self._path = path
            self._bed_width.setValue(profile.bed_width)
            self._bed_height.setValue(profile.bed_height)
            self._spacing.setValue(profile.spacing)
            idx = self._interpolation.findText(algo_name)
            if idx >= 0:
                self._interpolation.setCurrentIndex(idx)
            self._refresh_table()
            self._update_state()
            self._status.setText(f"Loaded: {path.name} ({profile.printer})")
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Load Error", f"Failed to load profile:\n{exc}")

    def _save_profile(self) -> None:
        if self._calibration is None:
            return
        if self._path is None:
            self._save_profile_as()
            return
        try:
            profile = self._calibration.to_profile()
            profile.printer = "User"
            profile.save(self._path)
            self._status.setText(f"Saved: {self._path.name}")
        except OSError as exc:
            QMessageBox.critical(self, "Save Error", f"Failed to save profile:\n{exc}")

    def _save_profile_as(self) -> None:
        if self._calibration is None:
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save Calibration Profile As", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            profile = self._calibration.to_profile()
            profile.printer = "User"
            profile.save(path)
            self._path = path
            self._update_state()
            self._status.setText(f"Saved: {path.name}")
        except OSError as exc:
            QMessageBox.critical(self, "Save Error", f"Failed to save profile:\n{exc}")

    # --- State ---

    def _update_state(self) -> None:
        has_cal = self._calibration is not None
        self._reset_btn.setEnabled(has_cal)
        self._apply_btn.setEnabled(has_cal)
        self._save_btn.setEnabled(has_cal)
        self._save_as_btn.setEnabled(has_cal)

    def get_calibration(self) -> Calibration | None:
        """Return the current calibration object."""
        return self._calibration

    def load_calibration(self, calibration: Calibration) -> None:
        """Load a calibration object directly."""
        self._calibration = calibration
        self._path = None
        mesh = calibration.mesh
        self._bed_width.setValue(mesh.width)
        self._bed_height.setValue(mesh.height)
        self._spacing.setValue(mesh.spacing)
        idx = self._interpolation.findText(calibration.interpolation.name())
        if idx >= 0:
            self._interpolation.setCurrentIndex(idx)
        self._refresh_table()
        self._update_state()
        self._status.setText(f"Calibration loaded ({mesh.num_points} points).")


__all__ = [
    "CalibrationEditor",
]
