import glob
import re
from typing import Dict, Iterable, List, Optional, Tuple

# TODO: Search only padding in file names. Add fullpath option just in case
# TODO: Work well with relative paths in nuke


# Version ---------------------------------------------------------------------
VERS_RE = re.compile(r"[vV](\d+)")
# Regex pattern for versions
# The first group is required and is used to capture the number.
# ex: v1, v01, v001, ...


def version_re_matches(path: str, pattern: re.Pattern = VERS_RE) -> List[re.Match]:
    """Find matches for version strings in a path

    Versions that do not match the last one are discarded.

    Args:
        path:       Path to inspect
        pattern:    Regex pattern capturing versions in the path.

    Returns:
        Ordered list of version Match objects
    """
    matches = list(pattern.finditer(path))
    if not matches:
        return []

    last_str = matches[-1].group(0)
    return [i for i in matches if i.group(0) == last_str]


def version_replace_str(path: str, repl: str, matches: List[re.Match]) -> str:
    """Replace verion sub-strings with a new one

    Args:
        path:       Path to operate on
        repl:       New full version string. ex: 'v005'
        matches:    Ordered list of captured versions.
    """
    res = path
    for m in reversed(matches):
        res = res[: m.start(0)] + repl + res[m.end(0) :]
    return res


def version_as_glob_expr(path: str, m: re.Match, offset: int = 0) -> str:
    """Replace verion sub-strings with a glob pattern

    The glob pattern is used to discover versions on disk
    ex: 'v01' -> 'v[0-9][0-9]'

    Args:
        path:   Path to operate on
        m:      Ordered list of captured versions.
                The Match objects mush have a group(1) than
                capures the number section of the version string.

    Returns:
        Path ready for a glob scan
    """
    padding = "[0-9]" * len(m.group(1))
    return path[: m.start(1) + offset] + padding + path[m.end(1) + offset :]


# Padding ---------------------------------------------------------------------
HASH_RE = re.compile(r"#{2,}")
# Regex pattern for hash frame padding
# Currently only match with a minimum of 2 '#' to avoid/limit conflicts.
# ex: ##, ####, ########, ...
STRF_RE = re.compile(r"%0(\d)d")
# Regex pattern for string format frame padding
# The first group is required and is used to capture the number.
# ex: %02d, %04d, %08d, ...


def pad_re_match(path: str, pattern: re.Pattern) -> Optional[re.Match]:
    """Find a frame padding sub-string in a path

    Only the last Match is returned

    Args:
        path:       Path to inspect
        pattern:    Regex pattern capturing frame padding in the path.

    Returns:
        A Match object capturing the padding. If nothing is found, None is returned
    """
    for m in reversed(list(pattern.finditer(path))):
        return m


def pad_re_match_resolved(
    path: str, patterns: Iterable[re.Pattern]
) -> Optional[re.Match]:
    """Like `pad_re_match` but iterates over all patterns in order until a match is found

    Args:
        path:       Path to inspect
        pattern:    Ordered list of regex pattern capturing frame padding in the path.

    Returns:
        A Match object capturing the padding. If nothing is found, None is returned
    """
    for pattern in patterns:
        m = pad_re_match(path, pattern)
        if m:
            return m


def pad_replace_str(path: str, repl: str, m: re.Match) -> str:
    """Replace the padding sub-string with a new one

    Args:
        path:   Path to operate on
        repl:   New full padding string. ex: '####', '1001'
        m:      Captured padding
    """
    return path[: m.start(0)] + repl + path[m.end(0) :]


def pad_as_glob_expr(path: str, m: re.Match, offset: int = 0) -> str:
    """Replace frame padding sub-strings with a glob pattern

    The glob pattern is used to discover versions on disk
    ex: 'file_####.exr' -> 'file_[0-9][0-9][0-9][0-9].exr'
    ex: 'file_%04d.exr' -> 'file_[0-9][0-9][0-9][0-9].exr'

    Args:
        path:   Path to operate on.
        m:      Captured frame padding.
                The Match object can have a group(1) that
                capures the char length of the padding.
        offset: Offset to apply to the Match span.
                Useful when doing multiple substitutions in chain that can
                each alter the string length.

    Returns:
        Path ready for a glob scan
    """
    try:
        size = int(m.group(1))
        start, end = m.span(0)
    except IndexError:
        size = len(m.group(0))
        start, end = m.span(0)
    start += offset
    end += offset
    padding = "[0-9]" * size
    return path[:start] + padding + path[end:]


# Scanning --------------------------------------------------------------------
VersionType = Tuple[str, Optional[str], List[str]]
# Type alias for an individual version
# (padded_path, version_str, frames)


def scan_versions(
    path: str,
    version_re: re.Pattern = VERS_RE,
    hash_re: re.Pattern = HASH_RE,
    strf_re: re.Pattern = STRF_RE,
) -> List[VersionType]:
    """Scan for existing versions on disk

    When a path does not contain a version,
    the returned list will at most contain 1 item.
    The `version_str` for that item will be None.

    The path may contain frame padding in hash(####) or strf(%04d) format.
    Discovered frames matching the padding will be added
    to the frames list of that version.
    If the path does not contain padding, the frames list will always be empty.

    Args:
        path:       Path to scan.
        version_re: Regex Pattern for version sub-strings.
                    The Match objects mush have a group(1) than
                    capures the number section of the version string.
        hash_re:    Regex pattern for hash frame padding.
        strf_re:    Regex pattern for string format frame padding.
                    The Match object must have a group(1) that
                    capures the char length of the padding.

    Returns:
        Ordered list of versions discovered. Each version is a VersionType.

        padded_path:    Original path with the version string replaced.
        version_str:    New version string. May be None if no version could be found.
        frames:         List of discovered frames if the path contained padding.
    """
    # Find matches
    version_matches = version_re_matches(path, version_re)
    pad_match = pad_re_match_resolved(path, (hash_re, strf_re))

    # Substitute patterns for glob expressions
    # An offset amount if tracked to adjust subsequent replace operations.
    # Replace operations are down backards where possible to avoid
    glob_expr = path
    offset_idx = 0
    offset_len = 0

    if pad_match:
        glob_expr = pad_as_glob_expr(glob_expr, pad_match)
        offset_idx = pad_match.start(0)
        offset_len = len(glob_expr) - len(path)

    if version_matches:
        for m in reversed(version_matches):
            offset = 0
            if m.start(0) > offset_idx:
                offset = offset_len
            glob_expr = version_as_glob_expr(glob_expr, m, offset=offset)

    # Scan existing files
    files = sorted(glob.glob(glob_expr))
    # for f in files:
    #     print("file:", f)

    # Group files by version
    offset_len = 0
    if pad_match:
        try:
            offset_len = int(pad_match.group(1)) - len(pad_match.group(0))
        except IndexError:
            offset_len = 0

    version_groups = _group_versions(files, version_matches, offset_idx, offset_len)
    # print("version_groups", version_groups)
    # for k, v in version_groups.items():
    #     print(k, ":")
    #     for _v in v:
    #         print("  ", _v)

    # Format the result
    if version_groups:
        return _format_result(version_groups, pad_match)
    return []


def _group_versions(
    paths: List[str],
    version_matches: List[re.Match],
    offset_idx: int,
    offset_len: int,
) -> Dict[str, List[str]]:
    """Group paths by their version string into a dictionary

    Args:
        paths:      Path to group
        version_re: Pattern for capturing version strings
    """
    groups = dict()
    for path in paths:
        # Find the version
        versions = []
        for m in version_matches:
            offset = 0
            if m.start(0) > offset_idx:
                offset = offset_len
            v = path[m.start(0) + offset : m.end(0) + offset]
            versions.append(v)
        # versions = [path[m.start(0) : m.end(0)] for m in version_matches]

        version = versions[-1] if versions else None
        # Discard files where version strings are not all equal
        if len(set(versions)) > 1:
            continue

        # Add to dict
        if version in groups.keys():
            groups[version].append(path)
        else:
            groups[version] = [path]
    return groups


def _format_result(
    version_groups: Dict[str, List[str]], m: Optional[re.Match]
) -> List[VersionType]:
    """Format the return value of scan_files

    Args:
        version_groups: Versions dictionary
        pad_match:      Regex Match object for frame padding
    """
    result = list()

    if m:
        pad_str = m.group(0)
        try:
            size = int(m.group(1))
            start, end = m.span(0)
            end = start + size
        except IndexError:
            size = len(m.group(0))
            start, end = m.span(0)

        for version_str in sorted(version_groups):
            version_files = version_groups[version_str]

            padded_path = version_files[0]
            padded_path = padded_path[:start] + pad_str + padded_path[end:]
            frames = []
            for file in version_files:
                frame_str = file[start:end]
                frames.append(frame_str)
            result.append((padded_path, version_str, frames))
    else:
        for version_str in sorted(version_groups):
            version_files = version_groups[version_str]

            padded_path = version_files[0]
            frames = []
            result.append((padded_path, version_str, frames))

    return result
