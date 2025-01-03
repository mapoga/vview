from pathlib import Path
import sys

from PySide2 import QtWidgets

from vview.core.scanner.plugins.minimal.scanner import MinimalVersionScanner

from vview.core.thumb.fake import FakeTumbCache
from vview.gui.main import select_related_version


def main():
    app = QtWidgets.QApplication(sys.argv)

    root_dir = None
    root_dir = str(Path(__file__).parent / "samples")
    path = "night_pano.jpg"
    # path = "night_pano_v01_##.jpg"
    # path = "night_pano_v01_022.jpg"
    path = "landscape_hd_v14.jpg"

    # scanner = MinimalVersionScanner(root_dir=root_dir)
    scanner = MinimalVersionScanner()
    thumb_cache = FakeTumbCache(delay=0.7, rand_delay=1.0)

    def on_preview_changed(_version, _is_preview):
        if _is_preview:
            print(scanner.version_pretty_str(_version))
        else:
            print("Preview: Off")

    version = select_related_version(
        # path,
        str(Path(root_dir) / path),
        scanner,
        thumb_enabled=True,
        thumb_cache=thumb_cache,
        preview_changed_fct=on_preview_changed,
    )
    print(scanner.version_pretty_str(version))
    sys.exit()


if __name__ == "__main__":
    main()
