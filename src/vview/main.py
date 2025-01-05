def launch(
    thumb_enabled: bool = True,
    thumb_reformat: str = "FILL",
    change_range: bool = True,
) -> None:
    """Configuration friendly alias for `choose_version_for_selected_nodes`"""

    from vview.gui.utils import ReformatType
    from vview.nk import choose_version_for_selected_nodes

    thumb_reformat_enum = ReformatType[thumb_reformat.upper()]

    choose_version_for_selected_nodes(thumb_enabled, thumb_reformat_enum, change_range)
