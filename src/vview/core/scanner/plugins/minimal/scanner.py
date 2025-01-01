import datetime
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from vview.core.scanner.interface import IVersionScanner
from vview.core.scanner.utils import format_frames

from .utils import (
    HASH_RE,
    STRF_RE,
    VERS_RE,
    VersionType,
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

    # Version attributes ------------------------------------------------------
    def get_version_name(self, version: VersionType) -> str:
        _, version_str, _ = version
        return version_str if version_str else "n/a"

    def get_version_path(self, version: VersionType) -> str:
        padded_path, _, _ = version
        return str(padded_path)

    def get_version_formatted_frames(self, version: VersionType) -> str:
        _, _, str_frames = version
        int_frames = [int(f) for f in str_frames]
        return format_frames(int_frames) or "n/a"

    def get_version_frame_range(
        self, version: VersionType
    ) -> Optional[Tuple[int, int]]:
        _, _, str_frames = version
        if str_frames:
            return int(str_frames[0]), int(str_frames[-1])

    def get_version_formatted_date(self, version: VersionType) -> str:
        padded_path, _, str_frames = version

        # Use the path as-is if there is no frame padding
        path = Path(padded_path)

        # Format the last frame if there is frame padding
        if str_frames:
            for pattern in self.padding_patterns:
                padding_match = re_match_padding(str(path), pattern)
                if padding_match:
                    path = Path(
                        replace_re_match(padded_path, str_frames[-1], padding_match)
                    )
                    break

        # Get timestamp from existing file
        if path and path.is_file():
            date = datetime.datetime.fromtimestamp(path.stat().st_mtime)
            return date.strftime("%Y-%m-%d %H:%M")

        return "n/a"

    # Path modification -------------------------------------------------------
    def replace_path_version(self, path: str, version_str: str) -> str:
        for pattern in self.version_patterns:
            version_matches = re_match_versions(path, pattern)
            if version_matches:
                for version_match in reversed(version_matches):
                    replace_re_match(path, version_str, version_match)
                return path
        return path
