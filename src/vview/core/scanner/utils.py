import math
from typing import List


def elide_middle(txt: str, width: int) -> str:
    if len(txt) > width:
        half = float(width) / 2
        a, b = math.floor(half), math.ceil(half)
        return txt[: a - 3] + " ... " + txt[len(txt) - b + 2 :]
    else:
        return txt.ljust(width)


def format_frames(frames: List[int], sep: str = " ") -> str:
    try:
        return format_frames_nk(frames, sep=sep)
    except ModuleNotFoundError:
        return format_frames_std(frames, sep=sep)


def format_frames_std(frames: List[int], sep: str = " ") -> str:
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


def format_frames_nk(frames: List[int], sep: str = " ") -> str:
    import nuke

    # Leverage nuke's ability to compact a list of frames incuding steps
    frames_str = [str(f) for f in frames]
    frame_ranges = nuke.FrameRanges(" ".join(frames_str))
    frame_ranges.compact()

    # Handle ranges of 1 frame
    parts = []
    for frame_range in frame_ranges:
        if frame_range.frames() == 1:
            parts.append(str(frame_range.first()))
        else:
            parts.append(str(frame_range))

    return sep.join(parts)


def _test_elide():
    print("test_elide")
    count = 20
    ref = "#" * count
    txt = "#" * (count + 1)
    print(ref)
    print(txt)
    print(elide_middle(txt, count))


def _test_format_frames():
    print("test_format_frames")
    frames = [1, 3, 5, 7, 8, 9, 10]
    print(frames)
    print(format_frames(frames))


def main():
    _test_elide()
    _test_format_frames()


if __name__ == "__main__":
    main()
