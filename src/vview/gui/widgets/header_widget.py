from enum import Enum

from PySide2 import QtCore, QtGui, QtWidgets

import vview.gui.resources  # noqa
from vview.gui.style import BASE_CSS, HEADER_CSS


class Pref(Enum):
    LIVE_PREVIEW = "pref_preview_enabled"
    SET_RANGE = "pref_range_enabled"
    SET_MISSING = "pref_missing_enabled"
    NESTED_NODES = "pref_nested_enabled"
    THUMBNAILS = "pref_thumb_enabled"


class HeaderWidget(QtWidgets.QWidget):
    """Bar at the top of the version dialog"""

    pref_changed = QtCore.Signal(object, bool)  # (Pref, enabled)

    def __init__(self, parent=None):
        super(HeaderWidget, self).__init__(parent=parent)

        self._info_opened = False

        self._init_ui()
        self._init_connect()
        self.set_index_info(0, 0)

    # Public ------------------------------------------------------------------
    def preference_enabled(self, pref: Pref) -> bool:
        return getattr(self, pref.value).isChecked()

    def set_preference_enabled(self, pref: Pref, enabled: bool) -> None:
        getattr(self, pref.value).setChecked(enabled)

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
        sides_width = 140

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
        self.index_QLabel.setMinimumWidth(sides_width)
        self.index_QLabel.setMaximumWidth(sides_width)
        layout.addWidget(self.index_QLabel)

        # Name QLabel
        self.name_QLabel = QtWidgets.QLabel("vview")
        self.name_QLabel.setObjectName("name_QLabel")
        self.name_QLabel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_QLabel)

        # Info Grp QWidget
        self.info_grp = QtWidgets.QWidget(parent=self)
        self.info_grp.setMinimumWidth(sides_width)
        self.info_grp.setMaximumWidth(sides_width)
        layout.addWidget(self.info_grp)

        # Info Grp Layout
        info_layout = QtWidgets.QHBoxLayout(self.info_grp)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        self.info_grp.setLayout(info_layout)

        # Preferences QPushButton
        self.pref_button = QtWidgets.QPushButton(parent=self)
        self.pref_button.setObjectName("pref_QPushButton")
        self.pref_button.setIcon(QtGui.QIcon(":bars-solid.svg"))
        self.pref_button.setIconSize(QtCore.QSize(18, 18))
        self.pref_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pref_button.setFlat(True)
        info_layout.addWidget(self.pref_button)

        # Preferences QMenu
        pref_menu = QtWidgets.QMenu("Preferences", parent=self.pref_button)
        pref_menu.setToolTipsVisible(True)
        self.pref_button.setMenu(pref_menu)
        self.pref_preview_enabled = QtWidgets.QAction(
            "Live Preview", parent=self.pref_button
        )
        self.pref_preview_enabled.setToolTip("Instantly update nodes.")
        self.pref_preview_enabled.setCheckable(True)
        self.pref_range_enabled = QtWidgets.QAction(
            "Edit Range", parent=self.pref_button
        )
        self.pref_range_enabled.setToolTip("Update the frame-range of Read nodes.")
        self.pref_range_enabled.setCheckable(True)
        self.pref_missing_enabled = QtWidgets.QAction(
            "Set Missing", parent=self.pref_button
        )
        self.pref_missing_enabled.setCheckable(True)
        self.pref_missing_enabled.setToolTip(
            "Change the version of nodes even if that version does not exist."
        )
        self.pref_nested_enabled = QtWidgets.QAction(
            "Nested Nodes", parent=self.pref_button
        )
        self.pref_nested_enabled.setCheckable(True)
        self.pref_nested_enabled.setToolTip(
            "Change the version of nodes inside groups recursively."
        )
        self.pref_thumb_enabled = QtWidgets.QAction(
            "Thumbnails", parent=self.pref_button
        )
        self.pref_thumb_enabled.setCheckable(True)
        self.pref_thumb_enabled.setToolTip("Show thumbnails.")
        pref_menu.addActions(
            (
                self.pref_preview_enabled,
                self.pref_range_enabled,
                self.pref_missing_enabled,
                self.pref_nested_enabled,
                self.pref_thumb_enabled,
            )
        )

        # Info QPushButton
        self.info_button = QtWidgets.QPushButton(parent=self)
        self.info_button.setObjectName("info_QPushButton")
        self.info_button.setIcon(QtGui.QIcon(":info.svg"))
        self.info_button.setIconSize(QtCore.QSize(18, 18))
        self.info_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.info_button.setFlat(True)
        self.info_button.setToolTip(self._tooltip_text())
        info_layout.addWidget(self.info_button)

        # Exit QPushButton
        self.exit_button = QtWidgets.QPushButton(parent=self)
        self.exit_button.setObjectName("exit_QPushButton")
        self.exit_button.setIcon(QtGui.QIcon(":xmark-solid.svg"))
        self.exit_button.setIconSize(QtCore.QSize(18, 18))
        self.exit_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exit_button.setFlat(True)
        self.exit_button.setToolTip("Press Escape or click away to close")
        info_layout.addWidget(self.exit_button)

        layout.setStretch(1, 1)

    def _init_connect(self):
        # Preferences
        self.pref_preview_enabled.toggled.connect(
            lambda enabled: self.pref_changed.emit(Pref.LIVE_PREVIEW, enabled)
        )
        self.pref_range_enabled.toggled.connect(
            lambda enabled: self.pref_changed.emit(Pref.SET_RANGE, enabled)
        )
        self.pref_missing_enabled.toggled.connect(
            lambda enabled: self.pref_changed.emit(Pref.SET_MISSING, enabled)
        )
        self.pref_nested_enabled.toggled.connect(
            lambda enabled: self.pref_changed.emit(Pref.NESTED_NODES, enabled)
        )
        self.pref_thumb_enabled.toggled.connect(
            lambda enabled: self.pref_changed.emit(Pref.THUMBNAILS, enabled)
        )

        self.info_button.clicked.connect(self._on_info_pressed)

    def _on_info_pressed(self):
        QtWidgets.QToolTip.showText(
            self.info_button.mapToGlobal(self.info_button.rect().center()),
            self._tooltip_text(),
            self.info_button,
            rect=self.info_button.rect(),
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
