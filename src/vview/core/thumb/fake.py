import random
import threading
import time
from typing import Callable, Optional

from vview.core.utils import padded_set_frame, strip_nuke_sequence

from .base import IThumbCache, FrameMode


class FakeTumbCache(IThumbCache):
    def __init__(self, delay: float = 0.5, rand_delay: float = 0.5):
        """A fake `IThumbCache` for testing outside of nuke

        Args:
            delay:      Fixed time delay simulating the work.
            rand_delay: Additionnal random time delay simulating the work.
        """
        self.delay = delay
        self.rand_delay = rand_delay

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
        if callback_args is None:
            callback_args = tuple()
        if callback_kwargs is None:
            callback_kwargs = dict()
        path = source

        # Convert a nuke sequence to a single frame
        # ex: 'name.####.exr 1-10' -> 'name.0001.exr'
        # ex: 'name.%02d.exr 1-10' -> 'name.01.exr'
        padded_path, start, _ = strip_nuke_sequence(path)
        if isinstance(start, int):
            path = padded_set_frame(padded_path, start)

        # Set delay
        delay = self.delay + random.random() * self.rand_delay

        # 'Work'
        def wait_delay():
            time.sleep(delay)
            if callable(callback):
                callback(path, *callback_args, **callback_kwargs)

        # Start thread
        thread = threading.Thread(target=wait_delay)
        thread.start()
