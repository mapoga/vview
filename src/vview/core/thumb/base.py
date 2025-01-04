from typing import Callable, Optional
from enum import Enum


class FrameMode(Enum):
    """Which frame inside a range to use for thumbnail"""

    FIRST = "first"
    MIDDLE = "middle"
    LAST = "last"
    CUSTOM = "custom"


class IThumbCache:
    """Handle the generation and caching of thumbnails"""

    def get_create(
        self,
        source: str,
        width: int = 100,
        height: int = 100,
        frame_mode: FrameMode = FrameMode.MIDDLE,
        custom_frame: int = 1,
        source_colorspace: Optional[str] = None,
        output_colorspace: Optional[str] = None,
        callback: Optional[Callable] = None,
        callback_args: Optional[tuple] = None,
        callback_kwargs: Optional[dict] = None,
    ) -> None:
        """Get a thumbnail from the cache or generate it if missing

        Once the subprocess has exited, `callback` will be called like so:
        `callback(output_path, *callback_args, **callback_kwargs)`

        The `output_path` should always be verified, as there is no guarantee
        of a successful export.

        Args:
            source:             Filepath to generate a thumbnail for.
                                Can be a nuke sequence ex: '/name_####.png 1-5'
            width:              Maximum width of the thumbnail.
                                The source ratio will be preserved.
            height:             Maximum heigth of the thumbnail.
                                The source ratio will be preserved.
            frame_mode:         Frame selection mode.
            custom_frame:       Frame to use when the frame_mode is FrameMode.CUSTOM
            source_colorspace:  Colorspace of the Read node.
            output_colorspace:  Colorspace of the Write node.
            callback:           Function to call when the generation is finished.
            callback_args:      Arguments for the callback
            callback_kwargs:    Keyword arguments for the callback
        """
        raise NotImplementedError
