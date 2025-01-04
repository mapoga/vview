from pathlib import Path
from typing import Any, Callable, Optional

from PySide2 import QtGui

from vview.core.scanner.interface import IVersionScanner
from vview.core.thumb.base import IThumbCache
from vview.core.utils import format_as_nuke_sequence
from vview.gui import VersionDialog, VersionItemWidget
from vview.gui.utils import ReformatType


def select_related_version(
    path: str,
    scanner: IVersionScanner,
    thumb_enabled: bool = False,
    thumb_cache: Optional[IThumbCache] = None,
    thumb_source_colorspace: Optional[str] = None,
    thumb_reformat: ReformatType = ReformatType.FILL,
    preview_changed_fct: Optional[Callable] = None,
) -> Any:
    """Opens a version chooser dialog and return the selected `version`

    Args:
        path:                       Path to scan.
        scanner:                    Version scanner instance.
        thumb_enabled:              True will show a thumbnail for versions.
        thumb_cache:                Thumbnail cache instance used to get or
                                    generate the thumbnails.
                                    Required when `thumb_enabled` is True.
        thumb_source_colorspace:    A nuke colorspace as from a Read node.
        thumb_reformat:             Type of thumbnail reformat.
        preview_changed_fct:        Function to call when:
                                    - The preview toggle is switched.
                                    - The selection has changed while the
                                    preview toggle is active.

    Returns:
        The selected `version`. It can be inspected using the scanner.
    """
    if thumb_enabled and not isinstance(thumb_cache, IThumbCache):
        raise TypeError(
            "When argument 'thumb_enabled' is True, "
            f"argument 'thumb_cache' must be of type '{IThumbCache}'. "
            f"Got '{type(thumb_cache)}'"
        )

    # Reverse the versions order since QListView cannot be visually reversed
    versions = scanner.scan_versions(path)
    versions.reverse()
    current_idx = 0

    # Setup selection changed callback
    def on_preview_changed(_idx, _is_preview):
        if callable(preview_changed_fct):
            _selected_version = versions[_idx] if versions else None
            preview_changed_fct(_selected_version, _is_preview)

    # Setup thumb created callback
    def add_thumb_pixmap(_output, _version_widget):
        if Path(_output).is_file():
            pixmap = QtGui.QPixmap.fromImage(_output)
            try:
                _version_widget.set_thumb_pixmap(pixmap)

            # Object was deleted. Dialog must have been closed.
            except RuntimeError:
                pass

    # Create dialog
    version_dialog = VersionDialog(preview_changed_fct=on_preview_changed)

    # Add versions
    for idx, version in enumerate(versions):
        # Create widget
        version_widget = VersionItemWidget(
            name=scanner.version_formatted_name(version),
            path=scanner.version_formatted_path(version),
            frames=scanner.version_formatted_frames(version),
            date=scanner.version_formatted_date(version),
            directory=str(Path(scanner.version_absolute_path(version)).parent),
            thumb_enabled=thumb_enabled,
            thumb_reformat=thumb_reformat,
        )
        version_dialog.list_widget.add_version(version_widget)

        # Check if its the original path
        if path == scanner.version_raw_path(version):
            current_idx = idx

        # Generate thumbnail
        if thumb_enabled:
            assert thumb_cache is not None

            # Format as a nuke sequence
            abs_p = scanner.version_absolute_path(version)
            frame_range = scanner.version_frame_range(version)
            if frame_range:
                abs_p = format_as_nuke_sequence(abs_p, frame_range[0], frame_range[1])

            # Launch sub-Process
            thumb_cache.get_create(
                source=abs_p,
                source_colorspace=thumb_source_colorspace,
                callback=add_thumb_pixmap,
                callback_args=(version_widget,),
            )

    # Select the initial path
    version_dialog.list_widget.set_selected_index(current_idx)

    # Resize
    version_dialog.adjustSize()
    size = version_dialog.size()
    version_dialog.resize(700, size.height())

    # Return the user selected version
    if version_dialog.exec_():
        if versions:
            idx = version_dialog.list_widget.selected_index()
            return versions[idx]
