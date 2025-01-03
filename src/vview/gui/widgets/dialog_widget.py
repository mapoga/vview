from typing import Callable, Optional

from PySide2 import QtCore, QtGui, QtWidgets

from vview.gui.widgets.header_widget import HeaderWidget
from vview.gui.widgets.list_widget import VersionListWidget


class VersionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        preview_changed_fct=Optional[Callable],
        parent=None,
    ):
        """Dialog to choose the version of a media

        The preview toggle is remembered.

        Args:
            preview_changed_fct:    Function to call when:
                                    - The preview toggle is switched.
                                    - The selection has changed while the
                                    preview toggle is active.
        """
        super(VersionDialog, self).__init__(parent=parent)
        self._preview_changed_fct = preview_changed_fct

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
        self.header.preview_toggle.stateChanged.connect(self._emit_preview_changed)

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
        # Trigger user callback
        if callable(self._preview_changed_fct):
            idx = self.list_widget.selected_index()
            is_preview = self.header.is_preview()
            self._preview_changed_fct(idx, is_preview)

    def _on_selection_changed(self):
        # Update index info in header
        index = self.list_widget.selected_index()
        length = self.list_widget.count()
        self.header.set_index_info(index, length)

        # Call preview changed
        if self.header.is_preview():
            self._emit_preview_changed()

    def write_settings(self):
        settings = QtCore.QSettings("mapoga", "vview")
        settings.setValue("preview", self.header.is_preview())

    def read_settings(self):
        settings = QtCore.QSettings("mapoga", "vview")
        self.header.set_is_preview(settings.value("preview", False, type=bool))

    def _on_finished(self, result: int):
        self.write_settings()
