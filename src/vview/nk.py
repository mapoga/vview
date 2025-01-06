from typing import Any, Dict, List, Optional, Sequence, Union

import nuke

from vview.core.scanner.interface import IVersionScanner
from vview.core.scanner.plugins.minimal.scanner import MinimalVersionScanner
from vview.core.thumb.base import IThumbCache
from vview.core.thumb.nk import temp_cache
from vview.core.utils import format_as_nuke_sequence
from vview.gui.main import select_related_version


MAIN_FILE_KNOB_NAME = "file"
FILE_KNOB_NAMES = ("proxy", "file")
RANGE_KNOB_NAMES = ("first", "last", "origfirst", "origlast")

# TODO: Fix toggle svg rendering black


def choose_version_for_selected_nodes() -> None:
    """Opens a version chooser dialog and apply the selection to the selected nodes

    Uses the `MinimalVersionScanner` and the global `temp_cache`.
    The primary filepath is taken from the first compatible node selected.
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
        thumb_cache=thumb_cache,
    )


def choose_version_for_nodes(
    nodes: Sequence[nuke.Node],
    scanner: IVersionScanner,
    thumb_cache: IThumbCache,
) -> None:
    """Opens a version chooser dialog and apply the selection to the nodes

    The primary filepath is taken from the first compatible node.

    Args:
        nodes:          Nodes to change version.
        scanner:        Version scanner instance.
        thumb_cache:    Thumbnail cache instance used to get or generate the thumbnails.
                        Required when `thumb_enabled` is True.
    """
    # Store original values
    orig_dicts = []
    for node in nodes:
        orig_dicts.append(save_knobs(node))

    # Pre-calculate all nodes versions.
    # Helps perform better when live preview is active at the cost of more work up front.
    nodes_versions = []
    for orig_dict in orig_dicts:
        file = orig_dict[MAIN_FILE_KNOB_NAME]
        node_versions = scanner.scan_versions(file)
        nodes_versions.append(node_versions)

    # Get the path to scan + colorspace
    path = ""
    source_colorspace = None
    for node, orig_dict in zip(nodes, orig_dicts):
        file = orig_dict[MAIN_FILE_KNOB_NAME]
        if file:
            path = file
            source_colorspace = get_node_colorspace(node)
            break

    # Setup live preview
    def on_preview_changed(_version: Any, _options: dict):
        # Signals that the update should restore
        if not _options["preview_enabled"]:
            _version = None

        for _node, _orig_dict, _versions in zip(nodes, orig_dicts, nodes_versions):
            update_node_version(
                _version,
                _node,
                _orig_dict,
                _versions,
                scanner,
                _options["range_enabled"],
                _options["set_missing_enabled"],
            )

    # User select version
    version, options = select_related_version(
        path,
        scanner,
        thumb_cache=thumb_cache,
        thumb_source_colorspace=source_colorspace,
        preview_changed_fct=on_preview_changed,
        parent=get_nuke_main_window(),
    )

    # Set the selected version
    for node, orig_dict, versions in zip(nodes, orig_dicts, nodes_versions):
        update_node_version(
            version,
            node,
            orig_dict,
            versions,
            scanner,
            options["range_enabled"],
            options["set_missing_enabled"],
        )


# Helpers ---------------------------------------------------------------------
def update_node_version(
    version: Any,
    node: nuke.Node,
    orig_dict: dict,
    node_versions: List[Any],
    scanner: IVersionScanner,
    range_enabled: bool,
    set_missing_enabled: bool,
):
    """Change or restore the knobs of a node based on a selected version

    Args:
        version:                Selected version. The version may not be related to this node.
        node:                   Node to modify.
        orig_dict:              Dictionnary of original knobs value for node.
        node_versions:          Scanned versions related to node.
        scanner:                Version scanner instance.
        range_enabled:          True will update the frame range of the node.
        set_missing_enabled:    Set the version name even if no version exists for that it.
    """
    # Dialog cancelled or preview is off. Restore
    if version is None:
        restore_knobs(node, orig_dict)
        return

    # Matching version found. Apply
    raw_name = scanner.version_raw_name(version)
    for node_version in node_versions:
        if scanner.version_raw_name(node_version) == raw_name:
            set_node_version(node, node_version, scanner, range_enabled)
            return

    # Path is versionned but is missing this specific version name
    if node_versions and scanner.version_contains_name(node_versions[0]):
        if set_missing_enabled:
            if isinstance(raw_name, str):
                set_node_version_name(node, raw_name, scanner)
                return
        else:
            restore_knobs(node, orig_dict)
            return

    # No match found. Restore
    restore_knobs(node, orig_dict)


def set_node_version_name(
    node: nuke.Node,
    version_name: str,
    scanner: IVersionScanner,
) -> None:
    """Change the filepath values of a node to a specific version name

    Args:
        node:           Node to modify.
        version_name:   New version name.
        scanner:        Version scanner instance.
    """
    for knob_name in FILE_KNOB_NAMES:
        knob = node.knob(knob_name)
        if knob and isinstance(knob, nuke.File_Knob):
            path = knob.value()
            if path:
                new_path = scanner.path_replace_version_name(path, version_name)
                if new_path != path:
                    knob.setValue(path)


def set_node_version(
    node: nuke.Node,
    version: Any,
    scanner: IVersionScanner,
    range_enabled: bool,
) -> None:
    """Set the knob values of a node based on a version

    Args:
        node:           Node to modify.
        version:        Version to apply.
        scanner:        Version scanner instance.
        range_enabled:  True will update the frame range of the node.
    """
    if not version:
        return
    contains_name = scanner.version_contains_name(version)
    version_raw_name = scanner.version_raw_name(version)
    frame_range = scanner.version_frame_range(version)

    # Set filepaths
    for knob_name in FILE_KNOB_NAMES:
        knob = node.knob(knob_name)
        if knob and isinstance(knob, nuke.File_Knob):
            path = knob.value()
            if path:
                if contains_name:
                    if isinstance(version_raw_name, str):
                        path = scanner.path_replace_version_name(path, version_raw_name)

                if range_enabled:
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
    for name in FILE_KNOB_NAMES + RANGE_KNOB_NAMES:
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


def get_nuke_main_window():
    from PySide2 import QtWidgets

    for obj in QtWidgets.QApplication.topLevelWidgets():
        if (
            obj.inherits("QMainWindow")
            and obj.metaObject().className() == "Foundry::UI::DockMainWindow"
        ):
            return obj
    raise RuntimeError("Could not find DockMainWindow instance")
