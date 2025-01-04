import datetime
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from vview.core.scanner.interface import IVersionScanner
from vview.core.utils import format_frames

from .core import (
    HASH_RE,
    STRF_RE,
    VERS_RE,
    VersionType,
    WorkingDirectory,
    re_match_padding,
    re_match_versions,
    replace_re_match,
    scan_versions,
)


class MinimalVersionScanner(IVersionScanner):
    def __init__(
        self,
        root_dir: Optional[str] = None,
        version_patterns: Optional[Iterable[re.Pattern]] = None,
        padding_patterns: Optional[Iterable[re.Pattern]] = None,
    ) -> None:
        """Version scanner implementation that aims to be as bare-bones as possible

        Args:
            root_dir:           Working directory for relative paths.
            version_patterns:   List of patterns that can capture the version sub-string(s).
                                Only the first pattern to work will be used.
                                version ex: 'v1', 'V1', 'v001', 'V00000001'
            padding_patterns:   List of patterns that can capture the padding sub-string.
                                Only the first pattern to work will be used.
                                padding ex: '##',   '####', '########'
                                            '%02d', '%04d', '%08d'
        """
        self.root_dir = root_dir
        self.version_patterns = (
            [VERS_RE] if version_patterns is None else version_patterns
        )
        self.padding_patterns = (
            [STRF_RE, HASH_RE] if padding_patterns is None else padding_patterns
        )

    # Scan --------------------------------------------------------------------
    def scan_versions(self, path: str) -> List[VersionType]:
        return scan_versions(
            path,
            root_dir=self.root_dir,
            version_patterns=self.version_patterns,
            padding_patterns=self.padding_patterns,
        )

    # Name --------------------------------------------------------------------
    def version_raw_name(self, version: VersionType) -> Optional[str]:
        return version[1]

    def version_contains_name(self, version: VersionType) -> bool:
        return self.version_raw_name(version) is None

    def version_formatted_name(self, version: VersionType) -> str:
        _, version_str, _ = version
        return version_str if version_str else "n/a"

    # Path --------------------------------------------------------------------
    def version_raw_path(self, version: VersionType) -> str:
        padded_path, _, _ = version
        return str(padded_path)

    def version_formatted_path(self, version: VersionType) -> str:
        return self.version_raw_path(version)

    def version_absolute_path(self, version: VersionType) -> str:
        padded_path, _, _ = version
        p = Path(str(padded_path))

        # Custom working directory
        if self.root_dir:
            if not p.is_absolute():
                with WorkingDirectory(self.root_dir):
                    p = p.absolute()
                return str(p)

        # Default working directory
        return str(p.absolute())

    def path_replace_version_name(self, path: str, version_str: str) -> str:
        for pattern in self.version_patterns:
            version_matches = re_match_versions(path, pattern)
            if version_matches:
                for version_match in reversed(version_matches):
                    path = replace_re_match(path, version_str, version_match)
                return path
        return path

    # Frames ------------------------------------------------------------------
    def version_frame_range(self, version: VersionType) -> Optional[Tuple[int, int]]:
        _, _, str_frames = version
        if str_frames:
            return int(str_frames[0]), int(str_frames[-1])

    def version_formatted_frames(self, version: VersionType) -> str:
        _, _, str_frames = version
        int_frames = [int(f) for f in str_frames]
        return format_frames(int_frames, sep=", ") or "n/a"

    # Date --------------------------------------------------------------------
    def version_formatted_date(self, version: VersionType) -> str:
        _, _, str_frames = version

        # Use the absolute path as-is if there is no frame padding
        path = self.version_absolute_path(version)

        # Format the last frame if there is frame padding
        if str_frames:
            for pattern in self.padding_patterns:
                padding_match = re_match_padding(path, pattern)
                if padding_match:
                    path = replace_re_match(path, str_frames[-1], padding_match)
                    break

        # Get timestamp from existing file
        path = Path(path)
        if path and path.is_file():
            date = datetime.datetime.fromtimestamp(path.stat().st_mtime)
            return date.strftime("%Y-%m-%d %H:%M")

        return "n/a"
