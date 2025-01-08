from typing import Any, Callable, Dict, List, Optional, Union

import nuke

from vview.core.scanner.interface import IVersionScanner
from vview.core.scanner.plugins.minimal.scanner import MinimalVersionScanner
from vview.core.thumb.base import IThumbCache
from vview.core.thumb.nk import temp_cache
from vview.core.utils import format_as_nuke_sequence
from vview.gui.main import ConcreteVersionDialog, Pref, ReformatType

MAIN_FILE_KNOB_NAME = "file"
FILE_KNOB_NAMES = ("proxy", "file")
RANGE_KNOB_NAMES = ("first", "last", "origfirst", "origlast")
THUMB_COMPATIBLE_NODE_TYPES = ("Read", "Write")


def choose_version_for_selected_nodes(
    node_sort_key_fct: Optional[Callable] = None,
) -> None:
    """Opens a version chooser dialog and apply the chosen version to the selected nodes

    Uses the `MinimalVersionScanner` and the global `temp_cache`.

    Args:
        node_sort_key_fct:  function to sort the selected nodes.

                            nodes_sort_key_fct(
                                node: nuke.node,
                                idx: int,
                                depth: int,
                            ) -> any

                            the first node in the resulting sorted list with a non-empty
                            "file" knob value will be chosen as the display node.
    """
    # Working directory for relative paths
    root_dir = None
    project_dir_knob = nuke.root()["project_directory"]
    if isinstance(project_dir_knob, nuke.File_Knob):
        root_dir = project_dir_knob.evaluate()
    if root_dir is None:
        root_dir = nuke.script_directory()

    # Scanner
    scanner = MinimalVersionScanner(root_dir=root_dir)

    # Nodes
    nodes = nuke.selectedNodes()
    nodes.reverse()

    # Nested nodes
    nested_nodes = []
    for node in nodes:
        nested_nodes.extend(get_node_children(node, recursive=True))

    # Dialog
    dialog = NodeVersionDialog(
        nodes,
        nested_nodes,
        scanner,
        temp_cache,
        node_sort_key_fct=node_sort_key_fct,
        parent=get_nuke_main_window(),
    )
    dialog.exec_()


class NodeVersionDialog(ConcreteVersionDialog):
    def __init__(
        self,
        nodes: List[nuke.Node],
        nested_nodes: List[nuke.Node],
        scanner: IVersionScanner,
        thumb_cache: IThumbCache,
        thumb_reformat: ReformatType = ReformatType.FILL,
        node_sort_key_fct: Optional[Callable] = None,
        parent=None,
    ):
        """Opens a version chooser dialog and apply the selection to the nodes

        Args:
            nodes:              Nodes to change version.
            nested_nodes:       Nodes grouped inside the primary nodes.
                                Those nodes will also have their versions changed
                                if the user has the feature enabled.
            scanner:            Version scanner instance.
            thumb_cache:        Thumbnail cache instance used to get or generate the thumbnails.
                                Required when `thumb_enabled` is True.
            thumb_reformat:     Type of thumbnail reformat.
            node_sort_key_fct:  function to sort the selected nodes.

                                nodes_sort_key_fct(
                                    node: nuke.node,
                                    idx: int,
                                    depth: int,
                                ) -> any

                                the first node in the resulting sorted list with a non-empty
                                "file" knob value will be chosen as the display node.
        """
        self._node_sort_key_fct = node_sort_key_fct

        self._nodes = nodes
        self._nested_nodes = nested_nodes

        # Store / Restore
        self._nodes_original_values = []
        self._nested_nodes_original_values = []

        # versions
        self._nodes_versions = []
        self._nested_nodes_versions = []
        self._versions_computed = False
        self._nested_versions_computed = False

        super().__init__(scanner, thumb_cache, thumb_reformat, parent=parent)
        self.__init_connects()
        self._store_original_values()
        self._compute_versions()
        self._populate()

    # Private -----------------------------------------------------------------
    def _store_original_values(self) -> None:
        """Store the knob values before any modification"""
        for node in self._nodes:
            values = save_knobs(node)
            self._nodes_original_values.append(values)

        for node in self._nested_nodes:
            values = save_knobs(node)
            self._nested_nodes_original_values.append(values)

    def _compute_versions(self) -> None:
        """Scan the nodes versions

        Notes:
            Nested versions are only scanned when required.
        """
        if not self._versions_computed:
            for node_original_values in self._nodes_original_values:
                file = node_original_values[MAIN_FILE_KNOB_NAME]
                versions = self.scanner.scan_versions(file)
                self._nodes_versions.append(versions)
            self._versions_computed = True

        if self.header.preference_enabled(Pref.NESTED_NODES):
            if not self._nested_versions_computed:
                for node_original_values in self._nested_nodes_original_values:
                    file = node_original_values[MAIN_FILE_KNOB_NAME]
                    versions = self.scanner.scan_versions(file)
                    self._nested_nodes_versions.append(versions)
                self._nested_versions_computed = True

    def _find_display_node(self) -> Optional[nuke.Node]:
        """Find a node to display its versions

        Notes:
            Users can provide a sort_key function to prioritize certain nodes.
        """
        # Build nodes list
        nodes = self._nodes.copy()
        if self.header.preference_enabled(Pref.NESTED_NODES):
            nodes.extend(self._nested_nodes)

        # Sort nodes
        key_fct = self._node_sort_key_fct
        if callable(key_fct):
            sort_keys = []
            for idx, node in enumerate(nodes):
                depth = len(node.fullName().split("."))
                sort_keys.append(key_fct(node, idx, depth))
            nodes = [n for _, n in sorted(zip(sort_keys, nodes))]

        # Find node with valid path
        for node in nodes:
            knob = node.knob(MAIN_FILE_KNOB_NAME)
            if isinstance(knob, nuke.File_Knob):
                path = knob.value()
                if path:
                    return node

    def _config_thumb(self, node: nuke.Node) -> None:
        """Configure values used in the thumbnail generation process based on the display node

        Args:
            node:   The display node.
        """
        if not node:
            return

        if isinstance(node, nuke.Node):
            knob = node.knob(MAIN_FILE_KNOB_NAME)
            if isinstance(knob, nuke.File_Knob):
                self.source_colorspace = get_node_colorspace(node)
                self.thumb_compatible = node.Class() in THUMB_COMPATIBLE_NODE_TYPES

    def _find_node_versions(self, node: nuke.Node) -> List[Any]:
        """Find the versions related to a node"""
        if not isinstance(node, nuke.Node):
            return []

        for idx, n in enumerate(self._nodes):
            if n == node:
                return self._nodes_versions[idx]

        for idx, n in enumerate(self._nested_nodes):
            if n == node:
                return self._nested_nodes_versions[idx]
        return []

    def _populate(self) -> None:
        """Add versions to the list widget"""
        # node
        display_node = self._find_display_node()
        if display_node is None:
            return

        # versions
        display_versions = self._find_node_versions(display_node)
        if not display_versions:
            return

        # Selection
        selected_version = None
        knob = display_node.knob(MAIN_FILE_KNOB_NAME)
        if isinstance(knob, nuke.File_Knob):
            path = knob.value()
            if path:
                for display_version in display_versions:
                    if path == self.scanner.version_raw_path(display_version):
                        selected_version = display_version
                        break

        # Colorspace + thumbnail compatibility
        self._config_thumb(display_node)

        # Populate
        for version in reversed(display_versions):
            self.add_version(version)

        # Select
        if selected_version is not None:
            self.select_version(selected_version)

        self.adjust_size()

    def _update_nodes_version(self, version: Any) -> None:
        """Update knob values based on a version"""
        # Nodes
        for idx, (node, versions) in enumerate(zip(self._nodes, self._nodes_versions)):
            update_node_version(
                version,
                node,
                self._nodes_original_values[idx],
                versions,
                self.scanner,
                self.header.preference_enabled(Pref.SET_RANGE),
                self.header.preference_enabled(Pref.SET_MISSING),
            )

        # Nested Nodes
        if self.header.preference_enabled(Pref.NESTED_NODES):
            for idx, (node, versions) in enumerate(
                zip(self._nested_nodes, self._nested_nodes_versions)
            ):
                update_node_version(
                    version,
                    node,
                    self._nested_nodes_original_values[idx],
                    versions,
                    self.scanner,
                    self.header.preference_enabled(Pref.SET_RANGE),
                    self.header.preference_enabled(Pref.SET_MISSING),
                )

    # Connections -------------------------------------------------------------
    def __init_connects(self) -> None:
        self.version_changed.connect(self.__on_version_changed)
        self.header.pref_changed.connect(self.__on_pref_changed)
        self.accepted.connect(self._on_accepted)
        self.rejected.connect(self._on_rejected)

    def __on_version_changed(self, version: Any) -> None:
        if self.header.preference_enabled(Pref.LIVE_PREVIEW):
            self._update_nodes_version(version)

    def __on_pref_changed(self, pref: Pref, enabled: bool) -> None:
        version = self.selected_version()

        if pref == Pref.LIVE_PREVIEW:
            if enabled:
                self._update_nodes_version(version)
            else:
                self._update_nodes_version(None)

        elif pref == Pref.SET_RANGE:
            if self.header.preference_enabled(Pref.LIVE_PREVIEW):
                self._update_nodes_version(version)

        elif pref == Pref.SET_MISSING:
            if self.header.preference_enabled(Pref.LIVE_PREVIEW):
                self._update_nodes_version(version)

        elif pref == Pref.NESTED_NODES:
            self.clear_versions()
            self._compute_versions()
            self._populate()

            if self.header.preference_enabled(Pref.LIVE_PREVIEW):
                version = self.selected_version()
                self._update_nodes_version(version)

    def _on_accepted(self) -> None:
        version = self.selected_version()
        self._update_nodes_version(version)

    def _on_rejected(self) -> None:
        self._update_nodes_version(None)


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
                    knob.setValue(new_path)


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


def get_node_children(node: nuke.Node, recursive: bool = False) -> List[nuke.Node]:
    children = []
    if isinstance(node, nuke.Group):
        children.extend(node.nodes())

    if recursive:
        for n in children.copy():
            children.extend(get_node_children(n, recursive=True))

    return children


def get_nuke_main_window():
    from PySide2 import QtWidgets

    for obj in QtWidgets.QApplication.topLevelWidgets():
        if (
            obj.inherits("QMainWindow")
            and obj.metaObject().className() == "Foundry::UI::DockMainWindow"
        ):
            return obj
    raise RuntimeError("Could not find DockMainWindow instance")
