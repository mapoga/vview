from pathlib import Path

from PySide2 import QtWidgets, QtGui, QtCore

from vview.gui.style import ICONS_DIR, BASE_CSS, HEADER_CSS


class HeaderWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HeaderWidget, self).__init__(parent=parent)
        self._init_ui()
        self._init_connect()

        self.set_index(0, 0)

    def set_index(self, index: int, length: int):
        """Update the index label"""
        txt = f"[{index}/{length}]"
        self.index_QLabel.setText(txt)

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.main.setLayout(layout)

        # Index QLabel
        self.index_QLabel = QtWidgets.QLabel("[0/0]")
        self.index_QLabel.setObjectName("index_QLabel")
        # Prevent changes in index to move the name away from the horizontal center
        self.index_QLabel.setMinimumWidth(120)
        self.index_QLabel.setMaximumWidth(120)
        layout.addWidget(self.index_QLabel)

        # Name QLabel
        self.name_QLabel = QtWidgets.QLabel("vview")
        self.name_QLabel.setObjectName("name_QLabel")
        self.name_QLabel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_QLabel)

        # Info Grp QWidget
        self.info_grp = QtWidgets.QWidget(parent=self)
        self.info_grp.setMinimumWidth(120)
        self.info_grp.setMaximumWidth(120)
        layout.addWidget(self.info_grp)

        # Info Grp Layout
        info_layout = QtWidgets.QHBoxLayout(self.info_grp)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        self.info_grp.setLayout(info_layout)

        # Info QLabel
        self.info_QLabel = QtWidgets.QLabel()
        self.info_QLabel.setObjectName("info_QLabel")
        info_pixmap = QtGui.QPixmap(str(Path(ICONS_DIR) / "info.svg"))
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
        # Enabling tracking is required to enable mouseMoveEvent
        # mouseMoveEvent is required to open tooltips faster
        self.setMouseTracking(True)
        self.main.setMouseTracking(True)
        self.info_grp.setMouseTracking(True)
        self.info_QLabel.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        super(HeaderWidget, self).mouseMoveEvent(event)

        # Workaround since the default tooltip is too slow to open
        if self.info_QLabel.underMouse():
            info_rect = self.info_QLabel.rect()
            pos = self.info_QLabel.mapToGlobal(info_rect.center())
            QtWidgets.QToolTip.showText(
                pos,
                self.tooltip_text(),
                self.info_QLabel,
            )

    @staticmethod
    def tooltip_text():
        return (
            "Shortcuts\n"
            "\n"
            "Next: Up,   Right\n"
            "Prev: Down, Left\n"
            "Max:  Ctrl + Up,   Ctrl + Right\n"
            "Min:  Ctrl + Down, Ctrl + Left\n"
            "\n"
            "Confirm: Enter\n"
            "Cancel:  Esc\n"
            "\n"
            "By: Mathieu Goulet-Aubin"
        )
