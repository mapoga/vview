"""
Module for generating thumbnails without blocking


Option 1.
Generate a temporary thumbnail and cache it for re-use.

```python
def print_path(output_path):
    if os.path.isfile(output_path):
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
    if os.path.isfile(output_path):
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

import os
import subprocess
import sys
import tempfile
import threading
import uuid
from collections import defaultdict
from enum import Enum
from typing import Callable, Optional, Tuple

import nuke


def get_node_sequence(node: nuke.Node) -> Optional[str]:
    """Return the sequence of a Read/Write node in nuke formatting

    ex: '/dirname/pathname_%04d.exr 1-10'
    """
    first = node.firstFrame()
    last = node.lastFrame()
    file = nuke.filename(node)
    if file:
        return f"{file} {first}-{last}"


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
        if knob.notDefault():
            return knob.value()


class FrameMode(Enum):
    FIRST = "first"
    MIDDLE = "middle"
    LAST = "last"
    CUSTOM = "custom"


class TempCache(object):
    ROOT_DIR = os.path.join(tempfile.gettempdir(), "vview")

    def __init__(self):
        """Manager for creating and caching temporary thumbnails

        The generated files are shared across cache instances in a tmp directory.
        """
        self._cache = dict()
        self._callbacks = defaultdict(list)

    def clear(self):
        """Clear the cache

        The files are not directly removed since other instances might be using them.
        The tmp directory is left to be managed by the OS.
        """
        self._cache.clear()
        self._callbacks.clear()

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
                                Can be a nuke sequence ex: '/path_####.png 1-5'
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
            if os.path.isfile(output):
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
        return os.path.join(cls.ROOT_DIR, name + ".png")

    def _process_finished(self, output, key):
        """This is run when thumbnail generation is complete"""

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
        # Its better to end with strings to avoid un-expected results
        popen_args = [
            f"{sys.executable}",
            "-t",
            f"{os.path.abspath(__file__)}",
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

        thread = threading.Thread(
            target=self._run_in_thread,
            args=(popen_args, callback, self._output, args, kwargs),
        )
        thread.start()

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
        write.knob("colorspace").setValue(output_colorspace)

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
    read.knob("file").fromUserText(source)
    if isinstance(source_colorspace, str):
        read.knob("colorspace").setValue(source_colorspace)

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

    if do_write_script:
        if os.path.isfile(write_script):
            os.remove(write_script)
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
    color_management = nuke.root().knob("colorManagement").value()
    ocio_config = nuke.root().knob("OCIO_config").value()
    custom_ocio_config = nuke.root().knob("customOCIOConfigPath").evaluate()
    return color_management, ocio_config, custom_ocio_config


def _set_color_management(
    color_management: Optional[str],
    ocio_config: Optional[str],
    custom_ocio_config: Optional[str],
):
    if isinstance(color_management, str):
        nuke.root().knob("colorManagement").setValue(color_management)
    if isinstance(ocio_config, str):
        nuke.root().knob("OCIO_config").setValue(ocio_config)
    if isinstance(custom_ocio_config, str):
        nuke.root().knob("customOCIOConfigPath").setValue(custom_ocio_config)


def main():
    """This module is meant to be used by the nuke command line to generate a thumbnail
    Its used by the `ThumbProcess` class.

    Users must avoid using an integer as the last argument since nuke will
    take it and use it for its own frame range.

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
