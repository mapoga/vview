import sys
from pathlib import Path
from typing import Any

from PySide2 import QtWidgets

from vview.core.scanner.plugins.minimal.scanner import MinimalVersionScanner
from vview.core.thumb.fake import FakeTumbCache
from vview.gui import ConcreteVersionDialog, Pref


def main():
    app = QtWidgets.QApplication(sys.argv)

    root_dir = None
    root_dir = str(Path(__file__).parent / "samples")
    path = "night_pano.jpg"
    # path = "night_pano_v01_##.jpg"
    # path = "night_pano_v01_022.jpg"
    path = "landscape_hd_v14.jpg"
    path = "landscape_v001_####.jpg"

    scanner = MinimalVersionScanner(root_dir=root_dir)
    versions = scanner.scan_versions(path)
    print(versions)
    thumb_cache = FakeTumbCache(delay=0.5, rand_delay=1.0)
    dialog = ConcreteVersionDialog(scanner, thumb_cache, thumb_compatible=True)

    def _on_version_changed(_version: Any):
        if dialog.header.preference_enabled(Pref.LIVE_PREVIEW):
            print(scanner.version_pretty_str(_version))
        else:
            print("Preview: Off")

        # if _version == versions[-1]:
        #     dialog.clear_versions()

    def _on_pref_changed(pref: Pref, enabled: bool):
        print("Preference changed", pref, enabled)
        if pref == Pref.NESTED_NODES:
            dialog.select_version(versions[1])

    dialog.version_changed.connect(_on_version_changed)
    dialog.header.pref_changed.connect(_on_pref_changed)

    for version in versions:
        dialog.add_version(version)
    dialog.adjust_size()
    dialog.exec_()
    sys.exit()


if __name__ == "__main__":
    main()
