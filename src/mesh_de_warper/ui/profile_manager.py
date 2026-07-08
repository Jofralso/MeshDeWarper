"""Profile management dialog for calibration profiles."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from mesh_de_warper.core.profile import CalibrationProfile

logger = logging.getLogger(__name__)


class ProfileManager(QDialog):
    """Dialog for managing calibration profiles.

    Supports loading recent profiles, viewing metadata,
    and deleting saved profiles.
    """

    def __init__(self, parent: object = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("Calibration Profile Manager")
        self.setMinimumSize(500, 400)

        self._selected_profile: CalibrationProfile | None = None
        self._selected_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Profile list
        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(QLabel("Saved Profiles:"))

        btn_row = QHBoxLayout()
        self._load_btn = QPushButton("Load from File...")
        self._load_btn.clicked.connect(self._load_from_file)
        btn_row.addWidget(self._load_btn)

        self._delete_btn = QPushButton("Delete Selected")
        self._delete_btn.clicked.connect(self._delete_selected)
        self._delete_btn.setEnabled(False)
        btn_row.addWidget(self._delete_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addWidget(self._list)

        # Metadata display
        self._info = QLabel("No profile selected.")
        self._info.setWordWrap(True)
        self._info.setAlignment(Qt.AlignTop)
        self._info.setFrameStyle(QLabel.Panel | QLabel.Sunken)
        layout.addWidget(self._info)

        # Dialog buttons
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.Open | QDialogButtonBox.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        self._button_box.button(QDialogButtonBox.Open).setEnabled(False)
        layout.addWidget(self._button_box)

    def _load_from_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Open Calibration Profile", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            profile = CalibrationProfile.load(path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Error", f"Failed to load profile:\n{exc}")
            return

        item = QListWidgetItem(f"{path.stem}  —  {profile.printer or 'unknown printer'}")
        item.setData(Qt.UserRole, str(path))
        self._list.addItem(item)
        self._list.setCurrentItem(item)

    def _on_selection_changed(self) -> None:
        item = self._list.currentItem()
        if item is None:
            self._delete_btn.setEnabled(False)
            self._button_box.button(QDialogButtonBox.Open).setEnabled(False)
            self._info.setText("No profile selected.")
            self._selected_profile = None
            self._selected_path = None
            return

        path_str = item.data(Qt.UserRole)
        if not path_str:
            return
        path = Path(path_str)
        try:
            profile = CalibrationProfile.load(path)
            self._selected_profile = profile
            self._selected_path = path
            self._delete_btn.setEnabled(True)
            self._button_box.button(QDialogButtonBox.Open).setEnabled(True)
            lines = [
                f"<b>Printer:</b> {profile.printer or 'N/A'}",
                f"<b>Bed:</b> {profile.bed_width} x {profile.bed_height} mm",
                f"<b>Spacing:</b> {profile.spacing} mm",
                f"<b>Interpolation:</b> {profile.interpolation}",
                f"<b>Points:</b> {len(profile.offsets)}",
                f"<b>Created:</b> {profile.created_at}",
                f"<b>Path:</b> {path}",
            ]
            self._info.setText("<br>".join(lines))
        except (OSError, ValueError):
            self._info.setText(f"<i>Could not load profile from {path}</i>")
            self._delete_btn.setEnabled(True)
            self._button_box.button(QDialogButtonBox.Open).setEnabled(True)

    def _delete_selected(self) -> None:
        item = self._list.currentItem()
        if item is None or self._selected_path is None:
            return
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Delete '{self._selected_path.name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return
        try:
            self._selected_path.unlink()
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Failed to delete file:\n{exc}")
            return
        row = self._list.row(item)
        self._list.takeItem(row)
        self._info.setText("Profile deleted.")
        self._selected_profile = None
        self._selected_path = None

    def get_selected_profile(self) -> CalibrationProfile | None:
        """Return the profile selected by the user."""
        return self._selected_profile

    def get_selected_path(self) -> Path | None:
        """Return the path of the selected profile."""
        return self._selected_path


__all__ = [
    "ProfileManager",
]
