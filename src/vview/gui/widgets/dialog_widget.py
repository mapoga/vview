from PySide2 import QtWidgets

from vview.gui.widgets.header_widget import HeaderWidget
from vview.gui.widgets.list_widget import VersionListWidget


class VersionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent=None,
    ):
        super(VersionDialog, self).__init__(parent=parent)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = HeaderWidget(parent=self)
        layout.addWidget(self.header)

        self.list_widget = VersionListWidget(parent=self)
        layout.addWidget(self.list_widget)

        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        index = self.list_widget.selected_index()
        if index < 0:
            index = 0
        else:
            index += 1
        length = self.list_widget.count()
        self.header.set_index(index, length)
