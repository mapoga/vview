from PySide2 import QtCore, QtGui, QtWidgets

import vview.gui.resources  # noqa
from vview.gui.style import BASE_CSS, HEADER_CSS


class HeaderWidget(QtWidgets.QWidget):
    """Bar at the top of the version dialog"""

    def __init__(self, parent=None):
        super(HeaderWidget, self).__init__(parent=parent)
        self._init_ui()
        self._init_connect()

        self.set_index_info(0, 0)

    # Public ------------------------------------------------------------------
    def is_preview(self) -> bool:
        """Check if the preview toggle is on"""
        return self.preview_toggle.isChecked()

    def set_is_preview(self, is_preview: bool):
        """Set the value of the preview toggle"""
        self.preview_toggle.setChecked(is_preview)

    def set_index_info(self, index: int, length: int):
        """Update the information section at the left

        Args:
            index:  Currently selected index.
            length: Amount of versions in the list.
        """
        index = max(0, index)
        txt = f"[{length-index}/{length}]"
        self.index_QLabel.setText(txt)

    # Private -----------------------------------------------------------------
    def _init_ui(self):
        self.setStyleSheet(BASE_CSS + HEADER_CSS)
        self.setMinimumHeight(26)
        self.setMaximumHeight(26)

        # Layout
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Main QWidget
        self.main = QtWidgets.QWidget(parent=self)
        self.main.setObjectName("main_QWidget")
        main_layout.addWidget(self.main)

        # Layout
        layout = QtWidgets.QHBoxLayout(self.main)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        self.main.setLayout(layout)

        # Index QLabel
        self.index_QLabel = QtWidgets.QLabel("[0/0]")
        self.index_QLabel.setObjectName("index_QLabel")
        # Prevent changes in index to move the name away from the horizontal center
        self.index_QLabel.setMinimumWidth(180)
        self.index_QLabel.setMaximumWidth(180)
        layout.addWidget(self.index_QLabel)

        # Name QLabel
        self.name_QLabel = QtWidgets.QLabel("vview")
        self.name_QLabel.setObjectName("name_QLabel")
        self.name_QLabel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_QLabel)

        # Info Grp QWidget
        self.info_grp = QtWidgets.QWidget(parent=self)
        self.info_grp.setMinimumWidth(180)
        self.info_grp.setMaximumWidth(180)
        layout.addWidget(self.info_grp)

        # Info Grp Layout
        info_layout = QtWidgets.QHBoxLayout(self.info_grp)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        self.info_grp.setLayout(info_layout)

        # Preview toggle
        self.preview_toggle = QtWidgets.QCheckBox(parent=self)
        self.preview_toggle.setObjectName("preview_QCheckBox")
        self.preview_toggle.setText("Preview")
        self.preview_toggle.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.preview_toggle.setFocusPolicy(QtCore.Qt.NoFocus)
        info_layout.addWidget(self.preview_toggle)

        # Info QLabel
        self.info_QLabel = QtWidgets.QLabel()
        self.info_QLabel.setObjectName("info_QLabel")
        info_pixmap = QtGui.QPixmap(":info.svg")
        info_pixmap = info_pixmap.scaled(
            18,
            18,
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )
        self.info_QLabel.setPixmap(info_pixmap)
        info_layout.addWidget(self.info_QLabel)
        info_layout.insertStretch(0, 1)

        layout.setStretch(1, 1)

    def _init_connect(self):
        # Workaround:
        # MouseMoveEvent is required to open tooltips at a custom speed(faster).
        # Tracking is required to enable mouseMoveEvent.
        self.setMouseTracking(True)
        self.main.setMouseTracking(True)
        self.info_grp.setMouseTracking(True)
        self.info_QLabel.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        super(HeaderWidget, self).mouseMoveEvent(event)

        # Workaround to open the tooltip faster than the default
        if self.info_QLabel.underMouse():
            info_rect = self.info_QLabel.rect()
            pos = self.info_QLabel.mapToGlobal(info_rect.center())
            QtWidgets.QToolTip.showText(
                pos,
                self._tooltip_text(),
                self.info_QLabel,
            )

    @staticmethod
    def _tooltip_text():
        return (
            "Next: Up,   Right\n"
            "Prev: Down, Left\n"
            "Max:  Ctrl + Up,   Ctrl + Right\n"
            "Min:  Ctrl + Down, Ctrl + Left\n"
            "\n"
            "Open: Ctrl + O\n"
            "\n"
            "Confirm: Enter\n"
            "Cancel:  Escape\n"
            "\n"
            "By: Mathieu Goulet-Aubin"
        )
