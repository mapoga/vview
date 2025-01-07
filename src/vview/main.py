from typing import Optional, Callable


def launch(node_sort_key_fct: Optional[Callable] = None) -> None:
    """Configuration friendly alias for `choose_version_for_selected_nodes`"""

    from vview.nk import choose_version_for_selected_nodes

    choose_version_for_selected_nodes(node_sort_key_fct=node_sort_key_fct)
