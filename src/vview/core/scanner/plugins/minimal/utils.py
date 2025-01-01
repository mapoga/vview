import os
import glob
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


VERS_RE = re.compile(r"[vV](\d+)")
# Regex pattern for versions
# The first capture group is required and is used to get the version number as an integer.
# ex: V1, v1, v01, v001, ...
HASH_RE = re.compile(r"#{2,}")
# Regex pattern for hash frame padding
# Currently only match with a minimum of 2 '#' to avoid/limit possible conflicts.
# ex: ##, ####, ########, ...
STRF_RE = re.compile(r"%0(\d)d")
# Regex pattern for string format frame padding
# The first capture group is required and is used to capture the size as an integer.
# ex: %02d, %04d, %08d, ...
VersionType = Tuple[str, Optional[str], List[str]]
# VersionType = (padded_path version_str, frames)
#
# padded_path:    Padded files path.
# version_str:    Full version string.
#                 None if no version could be found.
# frames:         List of discovered frame strings.
#                 None if the path does not contain padding.


# Utility ---------------------------------------------------------------------
def replace_re_match(
    string: str,
    repl: str,
    m: re.Match,
    group: int = 0,
    offset: int = 0,
) -> str:
    start = m.start(group) + offset
    end = m.end(group) + offset
    return string[:start] + repl + string[end:]


class WorkingDirectory:
    def __init__(self, working_directory: str) -> None:
        self._old = "."
        self._new = working_directory

    def __enter__(self):
        self._old = os.getcwd()
        os.chdir(self._new)

    def __exit__(self, _type, _value, _traceback):
        os.chdir(self._old)


# Version ---------------------------------------------------------------------
def re_match_versions(path: str, pattern: re.Pattern = VERS_RE) -> List[re.Match]:
    """Return captured versions in a path

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


def replace_version_by_glob(path: str, m: re.Match, offset: int = 0) -> str:
    """Replace a verion sub-string with a glob pattern

    The glob pattern is used to discover versions on disk
    ex: 'v01' -> 'v[0-9][0-9]'

    Args:
        path:   Path to operate on
        m:      Captured version.
                The Match object mush have a group(1) that
                captures the number part of the version string.
        offset: Moves the replace operation left/right.
    """
    padding = "[0-9]" * len(m.group(1))
    return replace_re_match(path, padding, m, group=1, offset=offset)


# Padding ---------------------------------------------------------------------
def re_match_padding(
    path: str,
    pattern: re.Pattern,
    fullpath: bool = False,
) -> Optional[re.Match]:
    """Return the last captured frame padding in a path

    Args:
        path:       Path to inspect
        pattern:    Regex pattern capturing a frame padding
        fullpath:   True will scan the whole path.
                    False will only scan the filename.
    """
    root_len = len(str(Path(path).parent))
    for m in reversed(list(pattern.finditer(path))):
        if fullpath or m.start(0) >= root_len:
            return m


def replace_padding_by_glob(path: str, m: re.Match, offset: int = 0) -> str:
    """Replace a frame padding sub-strings with a glob pattern

    The glob pattern is used to discover versions on disk
    ex: 'file_####.exr' -> 'file_[0-9][0-9][0-9][0-9].exr'
    ex: 'file_%04d.exr' -> 'file_[0-9][0-9][0-9][0-9].exr'

    Args:
        path:   Path to operate on.
        m:      Captured frame padding.
                If a group(1) exist, its value will be converted to integer and
                used to determine the size of the padding.
                Useful with `%02d` notation.
        offset: Moves the replace operation left/right.
                Useful when doing multiple substitutions in chain that can
                each alter the string length.
    """
    # Generate glob pattern
    try:
        size = int(m.group(1))
    except IndexError:
        size = len(m.group(0))
    padding = "[0-9]" * size

    return replace_re_match(path, padding, m, offset=offset)


# Scanning --------------------------------------------------------------------
def scan_versions(
    path: str,
    root_dir: Optional[str] = None,
    version_patterns: Optional[Iterable[re.Pattern]] = None,
    padding_patterns: Optional[Iterable[re.Pattern]] = None,
) -> List[VersionType]:
    """Scan for related versions that exist on disk

    Args:
        path:               Path to scan.
        root_dir:           Root directory for relative paths.
                            None will use the current working directory.
        version_patterns:   Regex Patterns for version sub-strings.
                            None will use the default: [VERS_RE]
                            The patterns MUST include a capture group(1)
                            to isolate the version number as an integer.
        padding_patterns:   Regex pattern for frame padding.
                            None will use the default: [STRF_RE, HASH_RE]
                            Patterns that expand to a different size MUST inlcude a
                            capture group(1) to isolate the expanded size.
                            ex: '%02d' may expand to the frame '34'
                            which has a different string length.

    Returns:
        Ordered list of versions discovered. Each version is a VersionType.

        padded_path:    Original path with the version string replaced.
        version_str:    Full version string.
                        None if no version could be found.
        frames:         List of discovered frame strings.
                        None if the path does not contain padding.
    """
    version_patterns = [VERS_RE] if version_patterns is None else version_patterns
    padding_patterns = (
        [STRF_RE, HASH_RE] if padding_patterns is None else padding_patterns
    )

    # Find version sub-string matches
    version_matches = []
    for pattern in version_patterns:
        version_matches = re_match_versions(path, pattern)
        if version_matches:
            break

    # Find a frame padding sub-string match
    padding_match = None
    for pattern in padding_patterns:
        padding_match = re_match_padding(path, pattern)
        if padding_match:
            break

    # Sort substitutions from back to front as to not disrupt operations
    match_tuples = [("version", m) for m in version_matches]
    if padding_match:
        match_tuples.append(("padding", padding_match))
    match_tuples.sort(key=lambda i: i[1].start(0), reverse=True)

    # Substitute version/padding for glob expressions.
    glob_expr = path
    for type_name, m in match_tuples:
        if type_name == "version":
            glob_expr = replace_version_by_glob(glob_expr, m)
        elif type_name == "padding":
            glob_expr = replace_padding_by_glob(glob_expr, m)

    # Scan existing files
    if root_dir:
        with WorkingDirectory(root_dir):
            files = sorted(glob.glob(glob_expr))
    else:
        files = sorted(glob.glob(glob_expr))
    # for f in files:
    #     print("file:", f)

    # Group by version
    version_groups = dict()
    for file in files:
        versions = _get_path_version_strings(file, version_matches, padding_match)
        # Discard files where version strings are not all equal
        if len(set(versions)) <= 1:
            version = versions[-1] if versions else None
            if version in version_groups.keys():
                version_groups[version].append(file)
            else:
                version_groups[version] = [file]
    # print("version_groups", version_groups)
    # for k, v in version_groups.items():
    #     print(k, ":")
    #     for _v in v:
    #         print("  ", _v)

    # Format the result
    if version_groups:
        return _format_result(version_groups, padding_match)
    return []


def _get_path_version_strings(
    path: str,
    version_matches: List[re.Match],
    padding_match: Optional[re.Match],
):
    # Calculate offset to apply to replace operations
    # that come after the padding operation.
    offset_idx = 0
    offset_len = 0
    if padding_match:
        offset_idx = padding_match.start(0)
        try:
            offset_len = int(padding_match.group(1)) - len(padding_match.group(0))
        except IndexError:
            offset_len = 0

    # Find the versions
    versions = []
    for m in version_matches:
        offset = 0
        if m.start(0) > offset_idx:
            offset = offset_len
        v = path[m.start(0) + offset : m.end(0) + offset]
        versions.append(v)
    return versions


def _format_result(
    version_groups: Dict[str, List[str]], padding_match: Optional[re.Match]
) -> List[VersionType]:
    """Format the return value of scan_files

    Args:
        version_groups: Versions dictionary
        pad_match:      Regex Match object for frame padding
    """
    result = list()

    if padding_match:
        pad_str = padding_match.group(0)
        try:
            size = int(padding_match.group(1))
            start, end = padding_match.span(0)
            end = start + size
        except IndexError:
            size = len(padding_match.group(0))
            start, end = padding_match.span(0)

        for version_str in sorted(version_groups):
            version_files = version_groups[version_str]

            # Replace back the padding
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
