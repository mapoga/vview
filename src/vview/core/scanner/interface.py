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

    # Version attributes ------------------------------------------------------
    @abstractmethod
    def get_version_name(self, version: Any) -> str:
        """Return the full version name of a `version`

        ex: 'v001'

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def get_version_path(self, version: Any) -> str:
        """Return the path of a `version`

        ex: 'file_v001_####.exr'

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def get_version_absolute_path(self, version: Any) -> str:
        """Return the absolute path of a `version`

        ex: '/root/path/to/file_v001_####.exr'

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def get_version_formatted_frames(self, version: Any) -> str:
        """Return the frames of a `version` formatted as a string

        ex: '1-5 7 9-10'

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    @abstractmethod
    def get_version_frame_range(self, version: Any) -> Optional[Tuple[int, int]]:
        """Return the frame range of a `version` if possible

        ex: (1, 10)

        Args:
            version: Version to inspect

        Return:
            first, last
        """
        raise NotImplementedError

    @abstractmethod
    def get_version_formatted_date(self, version: Any) -> str:
        """Return the timestamp of a `version` formatted as a string

        ex: 2025-01-01 02:21

        Args:
            version: Version to inspect
        """
        raise NotImplementedError

    # Path modification -------------------------------------------------------
    @abstractmethod
    def replace_path_version(self, path: str, version_str: str) -> str:
        """Replace the version sub-strings in a path

        ex: 'name_v001.png' -> 'name_v003.png'

        Args:
            path:           Path to modify.
            version_str:    Full string of the new version.

        Returns:
            Modified copy of the path
        """
        raise NotImplementedError

    def version_pretty_str(self, version: Any, max_len: int = 90) -> str:
        """Return a pretty string of the `version`

        Args:
            version:    Version to render.
            max_len:    Maximum string width.
        """
        if version is None:
            return str(None)

        name = self.get_version_name(version)
        dead_space = 15
        suffix_len = max_len - dead_space - len(name)

        frames = self.get_version_formatted_frames(version)
        frames = elide_middle(frames, suffix_len).ljust(suffix_len)
        path = self.get_version_path(version)
        path = elide_middle(path, suffix_len).ljust(suffix_len)
        date = self.get_version_formatted_date(version)
        date = elide_middle(date, suffix_len).ljust(suffix_len)

        txt = ""
        txt += f'| {" " * len(name)} | frames: {frames} |\n'
        txt += f"| {name} |   path: {path} |\n"
        txt += f'| {" " * len(name)} |   date: {date} |'
        return txt
