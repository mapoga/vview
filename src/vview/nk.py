from typing import Any, Dict, Optional, Sequence, Union, List

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

    # TODO: Handle thumbnails generation for reads without rgba channels like cryptomattes.
    # RuntimeError: Write1: /tmp/vview/c6d2cae9-5de3-5d42-b1ca-e9e769a43480.png: has no valid channels - nothing to write.
    # TODO: Give option to prioritize certain reads. aka: lower cryptomattes priority.
    nodes = nuke.selectedNodes()
    nodes.reverse()
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

    # Pre-calculate all nodes versions.
    # Helps perform better when live preview is active at the cost of more work up front.
    nodes_versions = []
    for orig_dict in orig_dicts:
        file = orig_dict["file"]
        node_versions = scanner.scan_versions(file)
        nodes_versions.append(node_versions)

    # Get the path to scan + colorspace
    path = ""
    source_colorspace = None
    for node, orig_dict in zip(nodes, orig_dicts):
        file = orig_dict["file"]
        if file:
            path = file
            source_colorspace = get_node_colorspace(node)
            break

    # Setup live preview
    def on_preview_changed(_version, _is_preview):
        if not _is_preview:
            # Signals that the update should restore
            _version = None

        for _node, _orig_dict, _versions in zip(nodes, orig_dicts, nodes_versions):
            update_node_version(
                _version,
                _node,
                _orig_dict,
                _versions,
                scanner,
                change_range,
            )

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
    for node, orig_dict, versions in zip(nodes, orig_dicts, nodes_versions):
        update_node_version(version, node, orig_dict, versions, scanner, change_range)


# Helpers ---------------------------------------------------------------------
def update_node_version(
    version: Any,
    node: nuke.Node,
    orig_dict: dict,
    node_versions: List[Any],
    scanner: IVersionScanner,
    change_range: bool,
):
    """Change or restore the knobs of a node based on a selected version

    Args:
        version:        Selected version. The version may not be related to this node.
        node:           Node to modify.
        orig_dict:      Dictionnary of original knobs value for node.
        node_versions:  Scanned versions related to node.
        scanner:        Version scanner instance.
        change_range:   True will update the frame range of the node.
    """
    # Dialog cancelled or preview is off. Restore
    if version is None:
        restore_knobs(node, orig_dict)
        return

    # Matching version found. Apply
    raw_name = scanner.version_raw_name(version)
    for node_version in node_versions:
        # TODO: Handle situations where a node may be versionned, but does not have this specific version.
        # The new version should still be set.
        # TODO: Offer option to take the nearest version?
        if scanner.version_raw_name(node_version) == raw_name:
            set_node_version(node, node_version, scanner, change_range)
            return

    # No match found. Restore
    restore_knobs(node, orig_dict)


def set_node_version(
    node: nuke.Node,
    version: Any,
    scanner: IVersionScanner,
    change_range: bool,
) -> None:
    """Set the knob values of a node based on a version

    Args:
        node:           Node to modify.
        version:        Version to apply.
        scanner:        Version scanner instance.
        change_range:   True will update the frame range of the node.
    """
    if not version:
        return
    contains_name = scanner.version_contains_name(version)
    version_raw_name = scanner.version_raw_name(version)
    frame_range = scanner.version_frame_range(version)

    # Set filepaths
    knob_names = ("proxy", "file")
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
                    # Wipe value first so that fromUserText will behave as expected
                    knob.setValue("")
                    knob.fromUserText(path)
                else:
                    knob.setValue(path)


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
        if isinstance(knob, nuke.Array_Knob):
            if knob.notDefault():
                return knob.value()
