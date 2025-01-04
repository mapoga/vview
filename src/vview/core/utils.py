import math
import re
from typing import List, Tuple, Optional


# String ----------------------------------------------------------------------
def elide_middle(txt: str, width: int) -> str:
    """Shorten text to fit within a certain width

    ex: '/my/looooooooooooooooooong/path.png' -> '/my/loo ... ng/path.png'

    Args:
        txt:    Text to elide.
        width:  Maximum character limit. Does not greedily fills empty space.
    """
    if len(txt) > width:
        half = float(width) / 2
        a, b = math.floor(half), math.ceil(half)
        return txt[: a - 3] + " ... " + txt[len(txt) - b + 2 :]
    else:
        return txt.ljust(width)


# Nuke sequence ---------------------------------------------------------------
def format_as_nuke_sequence(padded_path: str, start: int, end: int) -> str:
    return f"{padded_path} {start}-{end}"


def strip_nuke_sequence(nuke_sequence: str) -> Tuple[str, Optional[int], Optional[int]]:
    """Remove the frame range at the end of a nuke sequence

    ex: 'name.####.jpg 1-10' -> ('name.####.jpg', 1, 10)

    Returns:
        Stripped path, first, last
    """
    RE_RANGE = re.compile(r"\s(\d+)-(\d+)$")
    m = RE_RANGE.search(nuke_sequence)
    if m:
        return nuke_sequence[: m.start(0)], int(m.group(1)), int(m.group(2))
    return nuke_sequence, None, None


def padded_set_frame(padded_path: str, frame: int) -> str:
    """Replace the padding in a filepath by a specific frame

    ex: 'name.####.jpg' -> 'name.0001.jpg'
    ex: 'name.%02d.jpg' -> 'name.01.jpg'

    Args:
        padded_path:    Filepath.
        frame:          Frame to replace the padding with.
    """
    HASH_RE = re.compile(r"#{2,}")
    STRF_RE = re.compile(r"%0(\d)d")
    for pad_re in (STRF_RE, HASH_RE):
        pad_m_list = reversed(list(pad_re.finditer(padded_path)))
        if pad_m_list:
            for pad_m in pad_m_list:
                # Handle '####' and '%02d' format
                try:
                    size = int(pad_m.group(1))
                except IndexError:
                    size = len(pad_m.group(0))

                # Replace only the last padding occurence
                return (
                    padded_path[: pad_m.start(0)]
                    + str(frame).zfill(size)
                    + padded_path[pad_m.end(0) :]
                )
    return padded_path


# Format frame list -----------------------------------------------------------
def format_frames(frames: List[int], sep: str = ", ") -> str:
    try:
        return nuke_frames_formatting(frames, sep=sep)
    except ModuleNotFoundError:
        return basic_frames_formatting(frames, sep=sep)


def basic_frames_formatting(frames: List[int], sep: str = " ") -> str:
    """Basic frame formatting that only compact sub-ranges. Not steps.

    Args:
        frames: List of frames.
        sep:    Separator to use between sub-ranges.
    """
    start, end, parts = None, None, []

    for f in frames:
        if isinstance(end, int):
            if end + 1 == f:
                end += 1
            else:
                if start == end:
                    parts.append(str(start))
                else:
                    parts.append(f"{start}-{end}")
                start, end = f, f
        else:
            start, end = f, f

    if isinstance(end, int):
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}-{end}")

    return sep.join(parts)


def nuke_frames_formatting(frames: List[int], sep: str = " ") -> str:
    """Nuke's frame formatting

    Args:
        frames: List of frames.
        sep:    Separator to use between sub-ranges.
    """
    import nuke

    # Leverage nuke's ability to compact a list of frames incuding steps
    frames_str = [str(f) for f in frames]
    frame_ranges = nuke.FrameRanges(" ".join(frames_str))
    frame_ranges.compact()

    # Handle ranges of 1 frame more gracefully than nuke
    parts = []
    for frame_range in frame_ranges:
        if frame_range.frames() == 1:
            parts.append(str(frame_range.first()))
        else:
            parts.append(str(frame_range))

    return sep.join(parts)
