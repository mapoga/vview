from typing import Optional, Callable


def launch(display_node_fct: Optional[Callable] = None) -> None:
    """Configuration friendly alias for `choose_version_for_selected_nodes`"""

    from vview.nk import choose_version_for_selected_nodes

    if callable(display_node_fct):
        choose_version_for_selected_nodes(display_node_fct=display_node_fct)
    else:
        choose_version_for_selected_nodes()
