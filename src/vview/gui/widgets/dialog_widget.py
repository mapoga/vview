from PySide2 import QtCore, QtGui, QtWidgets

from vview.gui.widgets.header_widget import HeaderWidget, Pref
from vview.gui.widgets.list_widget import VersionListWidget


class VersionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """Dialog to choose the version of a media"""
        super(VersionDialog, self).__init__(parent=parent)

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
        self.setWindowFlags(QtGui.Qt.FramelessWindowHint | QtGui.Qt.Popup)

        self.list_widget.setFocus()

    def _init_connects(self):
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.finished.connect(self.write_settings)

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

        self.header.exit_button.pressed.connect(self.reject)

    def _on_selection_changed(self):
        # Update index info in header
        index = self.list_widget.selected_index()
        length = self.list_widget.count()
        self.header.set_index_info(index, length)

    def write_settings(self):
        settings = QtCore.QSettings("mapoga", "vview")

        for pref in Pref:
            settings.setValue(
                pref.value,
                self.header.preference_enabled(pref),
            )

    def read_settings(self):
        settings = QtCore.QSettings("mapoga", "vview")

        default_values = {}
        for pref in Pref:
            default_value = default_values.get(pref, True)
            settings_value = settings.value(pref.value, default_value, type=bool)
            self.header.set_preference_enabled(pref, settings_value)
