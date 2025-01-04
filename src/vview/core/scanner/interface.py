from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from vview.core.utils import elide_middle


class IVersionScanner(ABC):
    """Version scanner interface

    Serves as a communication layer between the GUI and the scanning process.
    A `version' can be anything as long as its understood by the implementation.
    """

    # Scan --------------------------------------------------------------------
    @abstractmethod
    def scan_versions(self, path: str) -> List[Any]:
        """Scan for existing `versions` on disk

        If the path is relative, the scanner should try and return relative paths as well.

        Args:
            path:   Path of the file to scan.
                    Expected to be taken from the file knob of a Read node.

        Returns:
            List of discovered `versions`
        """
        raise NotImplementedError

    # Name --------------------------------------------------------------------
    @abstractmethod
    def version_contains_name(self, version: Any) -> bool:
        """Check if the path contains a version sub-string

        Version-less paths should return False

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def version_raw_name(self, version: Any) -> Optional[str]:
        """Return the version name as scanned

        Version-less paths should return `None`

        ex: 'v001'

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def version_formatted_name(self, version: Any) -> str:
        """Return the name of a `version` for display purpose

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    # Path --------------------------------------------------------------------
    @abstractmethod
    def version_raw_path(self, version: Any) -> str:
        """Return the path of a `version` as scanned

        The path may be relative

        ex: 'file_v001_####.exr'

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def version_formatted_path(self, version: Any) -> str:
        """Return the path of a `version` for display purpose

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def version_absolute_path(self, version: Any) -> str:
        """Return the absolute path of a `version`

        ex: '/root/path/to/file_v001_####.exr'

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def path_replace_version_name(self, path: str, version_str: str) -> str:
        """Replace the version sub-strings in a path

        ex: 'name_v001.png' -> 'name_v003.png'

        Args:
            path:           Path to modify.
            version_str:    Full string of the new version.

        Returns:
            Modified copy of the path
        """
        raise NotImplementedError

    # Frames ------------------------------------------------------------------
    @abstractmethod
    def version_frame_range(self, version: Any) -> Optional[Tuple[int, int]]:
        """Return the frame range of a `version`

        Only medias with a padded path are expected to return a valid frame-range.
        Video or single frame images should return `None`.

        ex: (1, 10)

        Args:
            version: Version to inspect

        Return:
            first, last
        """
        raise NotImplementedError

    @abstractmethod
    def version_formatted_frames(self, version: Any) -> str:
        """Return the frames of a `version` formatted as a string

        ex: '1-5 7 9-10'

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    # Date --------------------------------------------------------------------
    @abstractmethod
    def version_formatted_date(self, version: Any) -> str:
        """Return the timestamp of a `version` formatted as a string

        ex: 2025-01-01 02:21

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    # Print -------------------------------------------------------------------
    def version_pretty_str(self, version: Any, max_len: int = 90) -> str:
        """Return a pretty string of the `version`

        Args:
            version:    Version to render.
            max_len:    Maximum string width.
        """
        if version is None:
            return str(None)

        name = self.version_formatted_name(version)
        dead_space = 15
        suffix_len = max_len - dead_space - len(name)

        frames = self.version_formatted_frames(version)
        frames = elide_middle(frames, suffix_len).ljust(suffix_len)
        path = self.version_formatted_path(version)
        path = elide_middle(path, suffix_len).ljust(suffix_len)
        date = self.version_formatted_date(version)
        date = elide_middle(date, suffix_len).ljust(suffix_len)

        txt = ""
        txt += f'| {" " * len(name)} | frames: {frames} |\n'
        txt += f"| {name} |   path: {path} |\n"
        txt += f'| {" " * len(name)} |   date: {date} |'
        return txt
