import datetime
import re
from pathlib import Path
from typing import List, Optional, Tuple

from vview.core.scanner.interface import IVersionScanner
from vview.core.scanner.utils import format_frames

from .utils import (
    HASH_RE,
    STRF_RE,
    VERS_RE,
    VersionType,
    pad_re_match_resolved,
    pad_replace_str,
    scan_versions,
    version_re_matches,
    version_replace_str,
)


class MinimalVersionScanner(IVersionScanner):
    def __init__(
        self,
        version_re: re.Pattern = VERS_RE,
        hash_re: re.Pattern = HASH_RE,
        strf_re: re.Pattern = STRF_RE,
    ) -> None:
        self.version_re = version_re
        self.hash_re = hash_re
        self.strf_re = strf_re

    # Scan --------------------------------------------------------------------
    def scan_versions(self, path: str) -> List[VersionType]:
        return scan_versions(
            path,
            version_re=self.version_re,
            hash_re=self.hash_re,
            strf_re=self.strf_re,
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
            m = pad_re_match_resolved(padded_path, (self.hash_re, self.strf_re))
            if m:
                path = Path(pad_replace_str(padded_path, str_frames[-1], m))

        # Get timestamp from existing file
        if path and path.is_file():
            date = datetime.datetime.fromtimestamp(path.stat().st_mtime)
            return date.strftime("%Y-%m-%d %H:%M")

        return "n/a"

    # Path modification -------------------------------------------------------
    def replace_path_version(self, path: str, version_str: str) -> str:
        m = version_re_matches(path, self.version_re)
        if m:
            return version_replace_str(path, version_str, m)
        else:
            return path
