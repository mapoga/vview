"""
Module for generating thumbnails from nuke without blocking


Option 1. (Preferred)
Generate a temporary thumbnail and cache it for re-use.

```python
def print_path(output_path):
    if Path(output_path).is_file():
        print(f'Successful thumbnail generation: {output_path}')
    else:
        print(f'Failed thumbnail generation:     {output_path}')

temp_cache.get_create(
    source='/dirname/filename_%04d.exr 1-10',
    width=200,
    height=200,
    callback=print_path,
)
```

Option 2.
Generate a thumbnail to a specific location.

```python
def print_path(output_path):
    if Path(output_path).is_file():
        print(f'Successful thumbnail generation: {output_path}')
    else:
        print(f'Failed thumbnail generation:     {output_path}')

p = ThumbProcess(
    source='/dirname/filename_%04d.exr 1-10',
    output='/dirname/filename_thumb.png',
    width=200,
    height=200,
)
p.run(callback=print_path)
```
"""

from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
import tempfile
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Callable, Optional, Tuple

import nuke

from vview.core.thumb.base import FrameMode, IThumbCache


# Thread Pool -----------------------------------------------------------------
thread_pool = ThreadPoolExecutor(max_workers=24)


class TempCache(IThumbCache):
    ROOT_DIR = Path(tempfile.gettempdir()) / "vview"

    def __init__(self):
        """Temporary thumbnails cache

        The files are stored in a temporary directory handled by the operating system.
        The OS will usually clear them after a reboot or a certain period.

        This cache is meant to be quick and re-use thumbnails created in previous
        nuke sessions as long as the OS decides to keep them.
        """
        self._cache = dict()
        self._callbacks = defaultdict(list)

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

        key = (
            source,
            width,
            height,
            frame_mode,
            custom_frame,
            source_colorspace,
            output_colorspace,
        )
        output = self._format_filepath(str(key))

        # Cache hit
        if key in self._cache.keys():
            # Subprocess is already running. Add to list of callbacks
            if self._cache[key] is None:
                self._callbacks[key].append((callback, callback_args, callback_kwargs))

            # Already processed. Call immediately
            else:
                if callable(callback):
                    callback(output, *callback_args, **callback_kwargs)

        # Cache miss
        else:
            # The file already exists. Add to cache. Call immediately
            if Path(output).is_file():
                self._cache[key] = output
                if callable(callback):
                    callback(output, *callback_args, **callback_kwargs)

            # Start processing
            else:
                # Set value to None to prevent multiple process for the same key
                self._cache[key] = None

                # Add callback for key
                self._callbacks[key].append((callback, callback_args, callback_kwargs))

                # Launch subprocess
                p = ThumbProcess(
                    source=source,
                    output=output,
                    width=width,
                    height=height,
                    frame_mode=frame_mode,
                    custom_frame=custom_frame,
                    source_colorspace=source_colorspace,
                    output_colorspace=output_colorspace,
                )
                p.run(self._process_finished, key)

    @classmethod
    def _format_filepath(cls, key_str: str):
        """Generate the filepath for a key"""
        name = str(uuid.uuid5(uuid.NAMESPACE_DNS, key_str))
        return str(Path(cls.ROOT_DIR) / (name + ".png"))

    def _process_finished(self, output, key):
        """This is run when a thumbnail generation is complete"""

        # Prevent new callbacks to be added
        self._cache[key] = output

        # Exaust all callbacks
        for callback, args, kwargs in self._callbacks[key]:
            if callable(callback):
                callback(output, *args, **kwargs)
        self._callbacks[key].clear()


class ThumbProcess(object):
    def __init__(
        self,
        source: str,
        output: str,
        width: int = 100,
        height: int = 100,
        frame_mode: FrameMode = FrameMode.MIDDLE,
        custom_frame: int = 1,
        source_colorspace: Optional[str] = None,
        output_colorspace: Optional[str] = None,
        write_script: Optional[str] = None,
    ):
        """Class for generating a thumbnail without blocking.

        Call `run()` on the instance to start the subprocess.

        When the subprocess generating the thumbnail has exited,
        a callback is called with the output path as the first argument.

        Args:
            source:             Filepath to generate a thumbnail for.
                                Can be a nuke sequence ex: '/path_####.png 1-5'
            output:             Filepath of the resulting thumbnail.
                                Must be a single image without padding.
            width:              Maximum width of the thumbnail.
                                The source ratio will be preserved.
            height:             Maximum heigth of the thumbnail.
                                The source ratio will be preserved.
            frame_mode:         Frame selection mode.
            custom_frame:       Frame to use when the frame_mode is FrameMode.CUSTOM
            source_colorspace:  Colorspace of the Read node.
            output_colorspace:  Colorspace of the Write node.
            write_script:       Filepath for writing the script used to generate the thumbnail
        """
        self._source = source
        self._output = output
        self._width = width
        self._height = height
        self._frame_mode = frame_mode
        self._custom_frame = custom_frame
        self._source_colorspace = source_colorspace
        self._output_colorspace = output_colorspace
        self._write_script = write_script

        management, config, custom = _get_color_management()
        self._color_management = management
        self._ocio_config = config
        self._ocio_custom = custom

    def run(self, callback: Optional[Callable] = None, *args, **kwargs):
        """Launches the subprocess

        Once the subprocess has exited, `callback` will be called like so:
        `callback(output_path, *args, **kwargs)`

        The `output_path` should always be verified, as there is no guarantee
        of a successful export.

        Args:
            callback: Function to call when the thumbnail generation has finished.
            *args:
            **kwargs:
        """
        # Nuke is tricky with its command line arguments.
        # Its better to end with strings to avoid un-expected results.
        # Set the numbers as early arguments.
        popen_args = [
            f"{sys.executable}",
            "-t",
            f"{Path(__file__).absolute()}",
            "-width",
            f"{self._width}",
            "-height",
            f"{self._height}",
            "-customFrame",
            f"{self._custom_frame}",
        ]

        # Optional args
        if isinstance(self._source_colorspace, str):
            popen_args.append("-sourceColorspace")
            popen_args.append(f"{self._source_colorspace}")
        if isinstance(self._output_colorspace, str):
            popen_args.append("-outputColorspace")
            popen_args.append(f"{self._output_colorspace}")
        if isinstance(self._color_management, str):
            popen_args.append("-colorManagement")
            popen_args.append(f"{self._color_management}")
        if isinstance(self._ocio_config, str):
            popen_args.append("-ocioConfig")
            popen_args.append(f"{self._ocio_config}")
        if isinstance(self._ocio_custom, str):
            popen_args.append("-customOcioConfig")
            popen_args.append(f"{self._ocio_custom}")
        if isinstance(self._write_script, str):
            popen_args.append("-writeScript")
            popen_args.append(f"{self._write_script}")

        # Must end in a string
        popen_args.extend(
            [
                "-frameMode",
                f"{self._frame_mode.value}",
                "-source",
                f"{self._source}",
                "-output",
                f"{self._output}",
            ]
        )

        thread_pool.submit(
            self._run_in_thread, popen_args, callback, self._output, args, kwargs
        )

    @staticmethod
    def _run_in_thread(popen_args, callback, output, args, kwargs):
        p = subprocess.Popen(popen_args, stdout=subprocess.DEVNULL)
        p.wait()
        if callable(callback):
            nuke.executeInMainThread(
                callback, args=(output,) + tuple(args), kwargs=kwargs
            )


def _write_node_thumbnail(
    node: nuke.Node,
    output: str,
    width: int = 100,
    height: int = 100,
    frame_mode: FrameMode = FrameMode.MIDDLE,
    custom_frame: int = 1,
    output_colorspace: Optional[str] = None,
    cleanup: bool = True,
):
    w, h = _max_size(node.width(), node.height(), width, height)
    frame = _calc_frame(node.firstFrame(), node.lastFrame(), frame_mode, custom_frame)

    reformat = nuke.nodes.Reformat(
        type="to box",
        box_width=w,
        box_height=h,
        box_fixed=True,
        resize="fit",
    )
    reformat.setInput(0, node)

    write = nuke.nodes.Write(file=output, create_directories=True)
    write.setInput(0, reformat)
    if isinstance(output_colorspace, str):
        write["colorspace"].setValue(output_colorspace)

    nuke.execute(write, frame, frame)

    if cleanup:
        nuke.delete(write)
        nuke.delete(reformat)


def _write_file_thumbnail(
    source: str,
    output: str,
    width: int = 100,
    height: int = 100,
    frame_mode: FrameMode = FrameMode.MIDDLE,
    custom_frame: int = 1,
    source_colorspace: Optional[str] = None,
    output_colorspace: Optional[str] = None,
    write_script: Optional[str] = None,
):
    do_write_script = isinstance(write_script, str) and write_script

    read = nuke.nodes.Read(on_error="nearest frame")
    file_knob = read["file"]
    assert isinstance(file_knob, nuke.File_Knob)
    file_knob.fromUserText(source)
    if isinstance(source_colorspace, str):
        read["colorspace"].setValue(source_colorspace)

    _write_node_thumbnail(
        read,
        output,
        width=width,
        height=height,
        frame_mode=frame_mode,
        custom_frame=custom_frame,
        output_colorspace=output_colorspace,
        cleanup=not do_write_script,
    )

    if isinstance(write_script, str) and write_script:
        script_path = Path(write_script)
        if script_path.is_file():
            script_path.unlink()
        nuke.scriptSaveToTemp(write_script)
    else:
        nuke.delete(read)


def _calc_frame(first: int, last: int, frame_mode: FrameMode, custom_frame: int) -> int:
    if frame_mode == FrameMode.CUSTOM:
        return custom_frame
    else:
        if frame_mode == FrameMode.FIRST:
            return first
        elif frame_mode == FrameMode.LAST:
            return last
        else:
            return first + int(float(last - first) / 2.0)


def _max_size(
    width: int, height: int, max_width: int, max_height: int
) -> Tuple[int, int]:
    """Scale a format to take as much space as possible inside some bounds
    while preserving its ratio.

    Args:
        width:      Initial width
        height:     Initial height
        max_width:  Bound for the width
        max_height: Bound for the height

    Returns:
        Scaled bounds
    """
    ratio = float(width) / float(height)
    max_ratio = float(max_width) / float(max_height)
    if max_ratio >= ratio:
        return int(float(max_height) * ratio), max_height
    else:
        return max_width, int(float(max_width) / ratio)


def _get_color_management() -> Tuple[str, str, str]:
    color_management = nuke.root()["colorManagement"].value()
    ocio_config = nuke.root()["OCIO_config"].value()
    custom_ocio_config_knob = nuke.root()["customOCIOConfigPath"]
    assert isinstance(custom_ocio_config_knob, nuke.File_Knob)
    custom_ocio_config = custom_ocio_config_knob.evaluate()
    return color_management, ocio_config, custom_ocio_config


def _set_color_management(
    color_management: Optional[str],
    ocio_config: Optional[str],
    custom_ocio_config: Optional[str],
):
    if isinstance(color_management, str):
        nuke.root()["colorManagement"].setValue(color_management)
    if isinstance(ocio_config, str):
        nuke.root()["OCIO_config"].setValue(ocio_config)
    if isinstance(custom_ocio_config, str):
        nuke.root()["customOCIOConfigPath"].setValue(custom_ocio_config)


def main():
    """This module is meant to be used by the nuke command line to generate a thumbnail
    Its used by the `ThumbProcess` class.

    Users must avoid using an integer as the last argument since nuke will
    strip it and use it for its own frame range.

    Examples:
        nuke -t this_module.py -width 200 -height 200 -source image.exr -output thumbnail.png
    """
    import argparse

    parser = argparse.ArgumentParser()
    # Required
    parser.add_argument("-source", type=str, required=True)
    parser.add_argument("-output", type=str, required=True)
    # Optional w Default
    parser.add_argument("-width", type=int, default=100)
    parser.add_argument("-height", type=int, default=100)
    parser.add_argument("-frameMode", type=str, default="middle")
    parser.add_argument("-customFrame", type=int, default=1)
    # Optional
    parser.add_argument("-sourceColorspace", type=str)
    parser.add_argument("-outputColorspace", type=str)
    parser.add_argument("-colorManagement", type=str)
    parser.add_argument("-ocioConfig", type=str)
    parser.add_argument("-customOcioConfig", type=str)
    parser.add_argument("-writeScript", type=str)
    args = parser.parse_args()

    _set_color_management(args.colorManagement, args.ocioConfig, args.customOcioConfig)
    _write_file_thumbnail(
        args.source,
        args.output,
        width=args.width,
        height=args.height,
        frame_mode=FrameMode(args.frameMode),
        custom_frame=args.customFrame,
        source_colorspace=args.sourceColorspace,
        output_colorspace=args.outputColorspace,
        write_script=args.writeScript,
    )


if __name__ == "__main__":
    main()
else:
    temp_cache = TempCache()
