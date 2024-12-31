from pathlib import Path
from PySide2 import QtGui


def _load_stylesheet(css_file: str) -> str:
    file_path = Path(css_file)
    if file_path.is_file():
        with open(css_file) as f:
            return f.read()
    return ""


def install_fonts():
    global FONTS_INSTALLED
    if FONTS_INSTALLED:
        return

    fonts_dir = Path(GUI_DIR) / "fonts"

    for child in fonts_dir.iterdir():
        if str(child).endswith(".ttf"):
            QtGui.QFontDatabase.addApplicationFont(str(child))

    FONTS_INSTALLED = True


FONTS_INSTALLED = False

GUI_DIR = str(Path(__file__).parent)
BASE_CSS = _load_stylesheet(str(Path(GUI_DIR) / "css" / "base.css"))
ITEM_CSS = _load_stylesheet(str(Path(GUI_DIR) / "css" / "item.css"))
LIST_CSS = _load_stylesheet(str(Path(GUI_DIR) / "css" / "list.css"))
HEADER_CSS = _load_stylesheet(str(Path(GUI_DIR) / "css" / "header.css"))
ICONS_DIR = str(Path(GUI_DIR) / "icons")
