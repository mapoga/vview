from pathlib import Path
from typing import Any, Optional

from PySide2 import QtCore, QtGui

from vview.core.scanner.interface import IVersionScanner
from vview.core.thumb.base import IThumbCache
from vview.core.utils import format_as_nuke_sequence

from .utils import ReformatType
from .widgets import Pref, VersionDialog, VersionItemWidget


class ConcreteVersionDialog(VersionDialog):
    version_changed = QtCore.Signal(object)  # (version)

    def __init__(
        self,
        scanner: IVersionScanner,
        thumb_cache: IThumbCache,
        thumb_reformat: ReformatType = ReformatType.FILL,
        thumb_source_colorspace: Optional[str] = None,
        thumb_compatible: bool = False,
        parent=None,
    ):
        """Version chooser dialog

        Args:
            scanner:                    Version scanner instance.
            thumb_cache:                Thumbnail cache instance used to get or
                                        generate the thumbnails.
            thumb_reformat:             Type of thumbnail reformat.
            thumb_source_colorspace:    A nuke colorspace as from a Read node.
            thumb_compatible:           True means that these versions can be rendered as an image.
                                        False will never try to generate thumbnails even
                                        if the user has thumbnails enabled.
        """
        self.scanner = scanner
        self.thumb_cache = thumb_cache
        self.thumb_reformat = thumb_reformat
        self.thumb_source_colorspace = thumb_source_colorspace
        self.thumb_compatible = thumb_compatible

        self._versions = []
        self._widgets = []

        super().__init__(parent=parent)

        default_width = 700
        self.adjustSize()
        size = self.size()
        self.resize(default_width, size.height())

    def adjust_size(self) -> None:
        self.setFixedHeight(self.sizeHint().height())

    # Version -----------------------------------------------------------------
    def add_version(self, version: Any) -> None:
        widget = VersionItemWidget(
            name=self.scanner.version_formatted_name(version),
            path=self.scanner.version_formatted_path(version),
            frames=self.scanner.version_formatted_frames(version),
            date=self.scanner.version_formatted_date(version),
            directory=str(Path(self.scanner.version_absolute_path(version)).parent),
            thumb_enabled=self.header.preference_enabled(Pref.THUMBNAILS),
            thumb_reformat=self.thumb_reformat,
        )

        if self.header.preference_enabled(Pref.THUMBNAILS):
            self._generate_thumbnail(version, widget)

        # Reverse the versions order since QListView cannot be visually reversed
        self._versions.append(version)
        self._widgets.append(widget)
        self.list_widget.add_version_item(widget)

    def clear_versions(self) -> None:
        self._versions.clear()
        self._widgets.clear()

        # Block the signals since its repeated during clear
        self.list_widget.setUpdatesEnabled(False)
        self.list_widget.blockSignals(True)

        self.list_widget.clear()

        self.list_widget.blockSignals(False)
        self.list_widget.setUpdatesEnabled(True)
        self.list_widget.update()
        # Force a signal after blocking the original ones
        self.list_widget.index_changed.emit(-1)

        self.adjust_size()

    def select_version(self, version: Any) -> None:
        for idx, _version in enumerate(self._versions):
            if _version == version:
                self.list_widget.set_selected_index(idx)
                return

    def selected_version(self) -> Optional[Any]:
        try:
            return self._versions[self.list_widget.selected_index()]
        except IndexError:
            return None

    # Private -----------------------------------------------------------------
    # Thumbnail ---------------------------------------------------------------
    def _on_thumb_enabled_changed(self, enabled: bool) -> None:
        for version, widget in zip(self._versions, self._widgets):
            if enabled:
                self._generate_thumbnail(version, widget)

            widget.set_thumb_enabled(enabled)

    def _generate_thumbnail(self, version: Any, widget: VersionItemWidget) -> None:
        if self.thumb_compatible:
            if widget.thumb_pixmap() is None:
                # Format as a nuke sequence
                path = self.scanner.version_absolute_path(version)
                frame_range = self.scanner.version_frame_range(version)
                if frame_range:
                    path = format_as_nuke_sequence(path, frame_range[0], frame_range[1])

                # Launch sub-Process
                self.thumb_cache.get_create(
                    source=path,
                    source_colorspace=self.thumb_source_colorspace,
                    callback=self._on_thumb_generated,
                    callback_args=(widget,),
                )

    def _on_thumb_generated(self, output: str, widget: VersionItemWidget) -> None:
        if Path(output).is_file():
            pixmap = QtGui.QPixmap(output)
            try:
                widget.set_thumb_pixmap(pixmap)

            # Object was deleted. Dialog must have been closed.
            except RuntimeError:
                pass

    # Connections -------------------------------------------------------------
    def _init_connects(self):
        super()._init_connects()
        self.header.pref_changed.connect(self._on_pref_changed)
        self.list_widget.index_changed.connect(self._on_index_changed)
        self.list_widget.index_added.connect(self.adjust_size)

    def _on_pref_changed(self, pref: Pref, enabled: bool) -> None:
        if pref == Pref.THUMBNAILS:
            self._on_thumb_enabled_changed(enabled)

    def _on_index_changed(self, idx: int) -> None:
        try:
            version = self._versions[idx]
        except IndexError:
            version = None
        self.version_changed.emit(version)
