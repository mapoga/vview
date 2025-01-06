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
    thumb_cache: IThumbCache,
    thumb_reformat: ReformatType = ReformatType.FILL,
    thumb_source_colorspace: Optional[str] = None,
    preview_changed_fct: Optional[Callable] = None,
    parent=None,
) -> Any:
    """Opens a version chooser dialog and return the selected `version`

    Args:
        path:                       Path to scan.
        scanner:                    Version scanner instance.
        thumb_cache:                Thumbnail cache instance used to get or
                                    generate the thumbnails.
                                    Required when `thumb_enabled` is True.
        thumb_reformat:             Type of thumbnail reformat.
        thumb_source_colorspace:    A nuke colorspace as from a Read node.
        preview_changed_fct:        Function to call when:
                                    - The preview toggle is switched.
                                    - The selection has changed while the
                                    preview toggle is active.

    Returns:
        The selected `version`. It can be inspected using the scanner.
    """

    # Reverse the versions order since QListView cannot be visually reversed
    versions = scanner.scan_versions(path)
    versions.reverse()
    current_idx = 0
    version_widgets = []

    # Setup selection changed callback
    def on_preview_changed(
        _idx: int,
        _preview_enabled: bool,
        _range_enabled: bool,
        _set_missing_enabled: bool,
    ):
        if callable(preview_changed_fct):
            _selected_version = versions[_idx] if versions else None
            preview_changed_fct(
                _selected_version,
                _preview_enabled,
                _range_enabled,
                _set_missing_enabled,
            )

    # Setup thumbnails enabled callback
    # Generate thumbnails if they do not already exist
    def on_thumb_enabled_changed(_thumb_enabled: bool):
        if _thumb_enabled:
            for _idx, _version_widget in enumerate(version_widgets):
                _version = versions[_idx]

                # Generate Pixmap
                if _version_widget.thumb_pixmap() is None:
                    # Format as a nuke sequence
                    _path = scanner.version_absolute_path(_version)
                    _frame_range = scanner.version_frame_range(_version)
                    if _frame_range:
                        _path = format_as_nuke_sequence(
                            _path, _frame_range[0], _frame_range[1]
                        )

                    # Launch sub-Process
                    thumb_cache.get_create(
                        source=_path,
                        source_colorspace=thumb_source_colorspace,
                        callback=add_thumb_pixmap,
                        callback_args=(_version_widget,),
                    )

                # Enable thumbnail
                _version_widget.set_thumb_enabled(True)

        # Disable thumbnail
        else:
            for version_widget in version_widgets:
                version_widget.set_thumb_enabled(False)

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
    version_dialog = VersionDialog(
        preview_changed_fct=on_preview_changed,
        thumb_enabled_changed_fct=on_thumb_enabled_changed,
        parent=parent,
    )

    # Add versions
    for idx, version in enumerate(versions):
        # Create widget
        version_widget = VersionItemWidget(
            name=scanner.version_formatted_name(version),
            path=scanner.version_formatted_path(version),
            frames=scanner.version_formatted_frames(version),
            date=scanner.version_formatted_date(version),
            directory=str(Path(scanner.version_absolute_path(version)).parent),
            thumb_enabled=False,
            thumb_reformat=thumb_reformat,
        )
        version_dialog.list_widget.add_version(version_widget)
        version_widgets.append(version_widget)

        # Check if its the original path
        if path == scanner.version_raw_path(version):
            current_idx = idx

    # Trigger generation
    if version_dialog.header.thumb_enabled():
        version_dialog.header.set_thumb_enabled(False)
        version_dialog.header.set_thumb_enabled(True)

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
