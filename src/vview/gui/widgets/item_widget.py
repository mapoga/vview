from pathlib import Path
from typing import Optional

from PySide2 import QtCore, QtGui, QtWidgets

import vview.gui.style
import vview.gui.utils
from vview.gui.utils import ReformatType
from .elided_label import ElidedLabel


class VersionItemWidget(QtWidgets.QWidget):
    _DEFAULT_PIXMAP = None

    def __init__(
        self,
        name: str = "",
        path: str = "",
        frames: str = "",
        date: str = "",
        thumb_enabled: bool = False,
        thumb_pixmap: Optional[QtGui.QPixmap] = None,
        thumb_reformat: ReformatType = ReformatType.FILL,
        thumb_width: int = 96,  # Roughly equates to a ratio of 16:9
        parent=None,
    ):
        """Widget representing a versionned media.

        Args:
            name:           Name of the version. ex: 'v001'
            path:           Path of the version. ex: '/path/to/render_%04d.exr'
            frames:         Available frames. ex: '1-10' or '1-3, 5, 9'
            date:           Timestamp of the media. ex: '2024-12-19 20:47'
            thumb_enabled:  True will display a thumbnail of the media.
            thumb_pixmap:   Thumbnail to dispalay.
            thumb_reformat: Thumbnail reformat type.
                            The available space is bound by the widget's height
                            and the `thumb_width` value.
            thumb_width:    Thumbnail width.
        """
        super(VersionItemWidget, self).__init__(parent=parent)

        vview.gui.style.install_fonts()
        self._init_ui()

        self._name: str = name
        self._path: str = path
        self._frames: str = frames
        self._date: str = date
        self._thumb_enabled: bool = thumb_enabled
        self._thumb_pixmap: Optional[QtGui.QPixmap] = None
        self._thumb_reformat: ReformatType = thumb_reformat
        self._thumb_width: int = thumb_width

        self.set_name(name)
        self.set_path(path)
        self.set_frames(frames)
        self.set_date(date)
        self.set_thumb_enabled(thumb_enabled)
        self.set_thumb_pixmap(thumb_pixmap)
        self.set_thumb_reformat(thumb_reformat)
        self.set_thumb_width(thumb_width)

    # Public -----------------------------------------------------------------
    def name(self) -> str:
        return self._name

    def set_name(self, name: str):
        self._name = name
        self.name_QLabel.setText(name)

    def path(self) -> str:
        return self._path

    def set_path(self, path: str):
        self._path = path
        self.path_value_QLabel.setText(path)
        self.path_value_QLabel.setToolTip(path)

    def frames(self) -> str:
        return self._frames

    def set_frames(self, frames: str):
        self._frames = frames
        self.frames_value_QLabel.setText(frames)

    def date(self) -> str:
        return self._date

    def set_date(self, date: str):
        self._date = date
        self.date_value_QLabel.setText(date)

    def thumb_enabled(self) -> bool:
        return self._thumb_enabled

    def set_thumb_enabled(self, is_enabled: bool):
        self._thumb_enabled = is_enabled
        self.thumbnail_QLabel.setVisible(is_enabled)
        self._refresh_pixamp()

    def thumb_pixmap(self) -> Optional[QtGui.QPixmap]:
        return self._thumb_pixmap

    def set_thumb_pixmap(self, thumb_pixmap: Optional[QtGui.QPixmap]):
        self._thumb_pixmap = thumb_pixmap
        self._refresh_pixamp()

    def thumb_reformat(self) -> ReformatType:
        return self._thumb_reformat

    def set_thumb_reformat(self, reformat: ReformatType):
        self._thumb_reformat = reformat
        self._refresh_pixamp()

    def thumb_width(self) -> int:
        return self._thumb_width

    def set_thumb_width(self, width: int):
        self._thumb_width = width
        self._refresh_pixamp()

    def open_directory(self):
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(str(Path(self.path()).parent))
        )

    # Re-Implemented Methods -------------------------------------------------
    def resizeEvent(self, event):
        super(VersionItemWidget, self).resizeEvent(event)

        self._refresh_pixamp()

    # Private ----------------------------------------------------------------
    def _set_selected(self, is_selected: bool):
        # Set a property used by the stylesheet
        self.setProperty("selected", is_selected)

        # Force widgets to update otherwise the stylesheet does not
        # get updated properties
        self._refresh_properties(self.name_QLabel)
        self._refresh_properties(self.frames_value_QLabel)
        self._refresh_properties(self.path_value_QLabel)
        self._refresh_properties(self.date_value_QLabel)

    @staticmethod
    def _refresh_properties(widget):
        # Force widgets to update otherwise the stylesheet does not
        # get updated properties
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _refresh_pixamp(self):
        """Update the content and size of the thumbnail"""
        size = QtCore.QSize(self.thumb_width(), self.size().height())
        pixmap = self.thumb_pixmap()

        if isinstance(pixmap, QtGui.QPixmap):
            pixmap = vview.gui.utils.reformat(pixmap, size, self.thumb_reformat())
        else:
            pixmap = vview.gui.utils.reformat(
                self._thumb_default(), size, ReformatType.FIT
            )

        self.thumbnail_QLabel.setPixmap(pixmap)

    def _init_ui(self):
        self.setStyleSheet(vview.gui.style.BASE_CSS + vview.gui.style.ITEM_CSS)
        self.setProperty("selected", False)

        # Overall layout
        overall_layout = QtWidgets.QHBoxLayout(self)
        overall_layout.setContentsMargins(0, 0, 12, 0)
        overall_layout.setSpacing(0)

        # Thumbnail
        self.thumbnail_QLabel = QtWidgets.QLabel()
        self.thumbnail_QLabel.setObjectName("thumbnail_QLabel")
        overall_layout.addWidget(self.thumbnail_QLabel)

        # --------------------------------------------------------------------
        # layout (name + info)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(18, 3, 5, 3)
        layout.setSpacing(12)
        overall_layout.addLayout(layout)

        # Name
        self.name_QLabel = QtWidgets.QLabel()
        self.name_QLabel.setObjectName("name_QLabel")
        layout.addWidget(self.name_QLabel)

        # Info layout --------------------------------------------------------
        self.info_widget = QtWidgets.QWidget()
        self.info_widget.setObjectName("info_QWidget")
        layout.addWidget(self.info_widget)

        self.info_layout = QtWidgets.QHBoxLayout()
        self.info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout.setSpacing(6)
        self.info_widget.setLayout(self.info_layout)
        layout.setStretch(2, 1)

        # Labels layout
        info_label_layout = QtWidgets.QVBoxLayout()
        info_label_layout.setContentsMargins(0, 0, 0, 0)
        info_label_layout.setSpacing(0)
        self.info_layout.addLayout(info_label_layout)

        # frames aabel
        self.frames_label_QLabel = QtWidgets.QLabel("frames")
        self.frames_label_QLabel.setObjectName("frames_label_QLabel")
        self.frames_label_QLabel.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        info_label_layout.addWidget(self.frames_label_QLabel)

        # path label
        self.path_label_QLabel = QtWidgets.QLabel("path")
        self.path_label_QLabel.setObjectName("path_label_QLabel")
        self.path_label_QLabel.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        info_label_layout.addWidget(self.path_label_QLabel)

        # date label
        self.date_label_QLabel = QtWidgets.QLabel("date")
        self.date_label_QLabel.setObjectName("date_label_QLabel")
        self.date_label_QLabel.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        info_label_layout.addWidget(self.date_label_QLabel)

        # Values layout ------------------------------------------------------
        info_right_layout = QtWidgets.QVBoxLayout()
        info_right_layout.setContentsMargins(0, 0, 0, 0)
        info_right_layout.setSpacing(0)
        self.info_layout.addLayout(info_right_layout)

        # frames
        frames_layout = QtWidgets.QHBoxLayout()
        info_right_layout.addLayout(frames_layout)

        # self.frames_value_QLabel = QtWidgets.QLabel()
        self.frames_value_QLabel = ElidedLabel()
        self.frames_value_QLabel.setElideMode(QtCore.Qt.ElideMiddle)
        self.frames_value_QLabel.setObjectName("frames_value_QLabel")
        frames_layout.addWidget(self.frames_value_QLabel)
        frames_layout.addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )

        # path
        path_layout = QtWidgets.QHBoxLayout()
        info_right_layout.addLayout(path_layout)

        self.path_value_QLabel = ElidedLabel()
        self.path_value_QLabel.setElideMode(QtCore.Qt.ElideLeft)
        self.path_value_QLabel.setHoverColor(QtGui.QColor(180, 180, 180))
        self.path_value_QLabel.setObjectName("path_value_QLabel")
        self.path_value_QLabel.pressed.connect(self._on_path_pressed)
        path_layout.addWidget(self.path_value_QLabel)
        path_layout.addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )

        # date
        self.date_value_QLabel = QtWidgets.QLabel()
        self.date_value_QLabel.setObjectName("date_value_QLabel")
        info_right_layout.addWidget(self.date_value_QLabel)

        self.info_layout.setStretch(1, 1)

    def _on_path_pressed(self):
        self.open_directory()

    def _thumb_default(self) -> QtGui.QPixmap:
        """Get the default thumbnail.

        Is shared across all instances for performance reasons.
        """
        if isinstance(self._DEFAULT_PIXMAP, QtGui.QPixmap):
            return self._DEFAULT_PIXMAP
        else:
            return vview.gui.utils.svg_to_pixmap(
                svg_file=str(Path(vview.gui.style.ICONS_DIR) / "image.svg"),
                size=QtCore.QSize(200, 200),
                fg_color=QtGui.QColor(255, 255, 255, 15),
                bg_color=QtGui.QColor(0, 0, 0, 1),
                scale=QtCore.QSizeF(0.8, 0.8),
            )
