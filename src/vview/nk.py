from typing import Any, Dict, Optional, Sequence, Union

import nuke

from vview.core.scanner.interface import IVersionScanner
from vview.core.scanner.plugins.minimal.scanner import MinimalVersionScanner
from vview.core.thumb.base import IThumbCache
from vview.core.thumb.nk import temp_cache
from vview.core.utils import format_as_nuke_sequence
from vview.gui.main import select_related_version
from vview.gui.utils import ReformatType


def choose_version_for_selected_nodes(
    thumb_enabled: bool = True,
    thumb_reformat: ReformatType = ReformatType.FILL,
    change_range: bool = True,
) -> None:
    """Opens a version chooser dialog and apply the selection to the selected nodes

    Uses the `MinimalVersionScanner` and the global `temp_cache`.
    The primary filepath is taken from the first compatible node selected.

    Args:
        thumb_enabled:  True will show a thumbnail for versions.
        thumb_reformat: Type of thumbnail reformat.
        change_range:   True will update the frame range of the nodes.
    """
    # Working directory
    root_dir = None
    project_dir_knob = nuke.root()["project_directory"]
    if isinstance(project_dir_knob, nuke.File_Knob):
        root_dir = project_dir_knob.evaluate()
    if root_dir is None:
        root_dir = nuke.script_directory()

    nodes = nuke.selectedNodes()
    scanner = MinimalVersionScanner(root_dir=root_dir)
    thumb_cache = temp_cache

    choose_version_for_nodes(
        nodes,
        scanner,
        thumb_enabled=thumb_enabled,
        thumb_cache=thumb_cache,
        thumb_reformat=thumb_reformat,
        change_range=change_range,
    )


def choose_version_for_nodes(
    nodes: Sequence[nuke.Node],
    scanner: IVersionScanner,
    thumb_enabled: bool = False,
    thumb_cache: Optional[IThumbCache] = None,
    thumb_reformat: ReformatType = ReformatType.FILL,
    change_range: bool = True,
) -> None:
    """Opens a version chooser dialog and apply the selection to the nodes

    The primary filepath is taken from the first compatible node.

    Args:
        nodes:          Nodes to change version.
        scanner:        Version scanner instance.
        thumb_enabled:  True will show a thumbnail for versions.
        thumb_cache:    Thumbnail cache instance used to get or generate the thumbnails.
                        Required when `thumb_enabled` is True.
        thumb_reformat: Type of thumbnail reformat.
        change_range:   True will update the frame range of the nodes.
    """
    # Store original values
    orig_dicts = []
    for node in nodes:
        orig_dicts.append(save_knobs(node))

    # Pre-calculate nodes versions.
    # Helps perform better when live preview is active
    # at the cost of more work up front.
    nodes_versions = []
    for idx, node in enumerate(nodes):
        file = orig_dicts[idx]
        node_versions = scanner.scan_versions(file)
        nodes_versions.append(node_versions)

    # Get the path to scan + colorspace
    path = ""
    source_colorspace = None
    for idx, orig_dict in enumerate(orig_dicts):
        file = orig_dict["file"]
        if file:
            path = file
            source_colorspace = get_node_colorspace(nodes[idx])
            break

    # Setup live preview
    def on_preview_changed(_version, _is_preview):
        # Preview
        if _is_preview:
            _version_raw_name = scanner.version_raw_name(_version)
            for _idx, _node in enumerate(nodes):
                _node_version = nodes_versions[_idx].get(_version_raw_name)
                if _node_version is None:
                    restore_knobs(_node, orig_dicts[_idx])
                else:
                    set_node_version(_node, _node_version, scanner, change_range)
        # Restore
        else:
            for _idx, _node in enumerate(nodes):
                restore_knobs(_node, orig_dicts[_idx])

    # User select version
    version = select_related_version(
        path,
        scanner,
        thumb_enabled=thumb_enabled,
        thumb_cache=thumb_cache,
        thumb_source_colorspace=source_colorspace,
        thumb_reformat=thumb_reformat,
        preview_changed_fct=on_preview_changed,
    )

    # Set the selected version
    if version:
        version_raw_name = scanner.version_raw_name(version)
        for idx, node in enumerate(nodes):
            node_versions = nodes_versions[idx]
            node_version = node_versions.get(version_raw_name)
            if node_version is None:
                restore_knobs(node, orig_dicts[idx])
            else:
                set_node_version(node, node_version, scanner, change_range)
    # Restore original values
    else:
        for _idx, _node in enumerate(nodes):
            restore_knobs(_node, orig_dicts[_idx])


# Helpers ---------------------------------------------------------------------
def save_knobs(node: nuke.Node) -> Dict[str, Union[str, int]]:
    """Build a dictionnary of knob values"""
    values = dict()
    names = ["file", "proxy", "first", "last", "origfirst", "origlast"]
    for name in names:
        knob = node.knob(name)
        value = None
        if knob:
            value = knob.value()
        values[name] = value
    return values


def restore_knobs(node: nuke.Node, knob_dict: Dict[str, Union[str, int]]) -> None:
    """Restore knob values from a dictionnary"""
    for key, val in knob_dict.items():
        knob = node.knob(key)
        if knob and val is not None:
            knob.setValue(val)


def get_node_colorspace(node: nuke.Node) -> Optional[str]:
    """Return the colorspace of a Read/Write node

    None is returned if the default value is used or the knob does not exists.

    Note:
        Setting a colorspace knob to its default value when using
        nuke's command line will raise an exception.
        For that reason, it' best not to set default values.
    """
    knob = node.knob("colorspace")
    if knob:
        assert isinstance(knob, nuke.Pulldown_Knob)
        if knob.notDefault():
            return knob.value()


def set_node_version(
    node: nuke.Node,
    version: Any,
    scanner: IVersionScanner,
    change_range: bool,
) -> None:
    if not version:
        return
    contains_name = scanner.version_contains_name(version)
    version_raw_name = scanner.version_raw_name(version)
    frame_range = scanner.version_frame_range(version)

    # Set filepaths
    knob_names = ("file", "proxy")
    for knob_name in knob_names:
        knob = node.knob(knob_name)
        if knob and isinstance(knob, nuke.File_Knob):
            path = knob.value()
            if path:
                if contains_name:
                    if isinstance(version_raw_name, str):
                        path = scanner.path_replace_version_name(path, version_raw_name)

                if change_range:
                    if frame_range:
                        path = format_as_nuke_sequence(
                            path, frame_range[0], frame_range[1]
                        )
                    knob.fromUserText(path)
                else:
                    knob.setValue(path)
