from typing import Callable, Optional

from PySide2 import QtCore, QtGui, QtWidgets

from vview.gui.widgets.header_widget import HeaderWidget
from vview.gui.widgets.list_widget import VersionListWidget


class VersionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        preview_changed_fct: Optional[Callable] = None,
        thumb_enabled_changed_fct: Optional[Callable] = None,
        parent=None,
    ):
        """Dialog to choose the version of a media

        Args:
            preview_changed_fct:    Function to call when:
                                    - Preview enabled preference has been changed.
                                    - The selection has changed while preview enabled is checked.
            thumb_changed_fct:      Function to call when:
                                    - Thumbnails enabled preference hase been changed
                                    - Thumbnails reformat type preference has been changed.
        """
        super(VersionDialog, self).__init__(parent=parent)
        self._preview_changed_fct = preview_changed_fct
        self._thumb_enabled_changed_fct = thumb_enabled_changed_fct

        self._init_ui()
        self._init_connects()
        self.read_settings()

    def _init_ui(self):
        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = HeaderWidget(parent=self)
        layout.addWidget(self.header)

        # List
        self.list_widget = VersionListWidget(parent=self)
        layout.addWidget(self.list_widget)

        # Window flags
        self.setModal(True)
        self.setWindowFlags(QtGui.Qt.FramelessWindowHint | QtGui.Qt.Dialog)

    def _init_connects(self):
        # Preview changed
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        # Preview
        self.header.pref_preview_enabled_changed.connect(self._emit_preview_changed)
        self.header.pref_range_enabled_changed.connect(self._emit_preview_changed)
        self.header.pref_set_missing_changed.connect(self._emit_preview_changed)
        # Thumbnails
        self.header.pref_thumb_enabled_changed.connect(self._emit_thumb_enabled_changed)

        # Accept trigger
        accept_act = QtWidgets.QAction("Accept", parent=self)
        accept_act.setShortcuts(
            [
                QtGui.QKeySequence("Return"),
                QtGui.QKeySequence("Enter"),
            ]
        )
        accept_act.triggered.connect(self.accept)
        self.addAction(accept_act)

        self.finished.connect(self._on_finished)

    def _emit_preview_changed(self):
        if callable(self._preview_changed_fct):
            idx = self.list_widget.selected_index()
            preview_enabled = self.header.preview_enabled()
            range_enabled = self.header.range_enabled()
            set_missing_enabled = self.header.set_missing_enabled()
            self._preview_changed_fct(
                idx,
                preview_enabled,
                range_enabled,
                set_missing_enabled,
            )

    def _emit_thumb_enabled_changed(self, value):
        if callable(self._thumb_enabled_changed_fct):
            thumb_enabled = self.header.thumb_enabled()
            self._thumb_enabled_changed_fct(thumb_enabled)

    def _on_selection_changed(self):
        # Update index info in header
        index = self.list_widget.selected_index()
        length = self.list_widget.count()
        self.header.set_index_info(index, length)

        # Call preview changed
        if self.header.preview_enabled():
            self._emit_preview_changed()

    def write_settings(self):
        settings = QtCore.QSettings("mapoga", "vview")
        settings.setValue("preview_enabled", self.header.preview_enabled())
        settings.setValue("range_enabled", self.header.range_enabled())
        settings.setValue("set_missing_enabled", self.header.set_missing_enabled())
        settings.setValue("thumb_enabled", self.header.thumb_enabled())

    def read_settings(self):
        settings = QtCore.QSettings("mapoga", "vview")
        self.header.set_preview_enabled(
            settings.value("preview_enabled", True, type=bool)
        )
        self.header.set_range_enabled(settings.value("range_enabled", True, type=bool))
        self.header.set_set_missing_enabled(
            settings.value("set_missing_enabled", True, type=bool)
        )
        self.header.set_thumb_enabled(settings.value("thumb_enabled", True, type=bool))

    def _on_finished(self, result: int):
        self.write_settings()
