from pathlib import Path
from PySide2 import QtGui


def _load_stylesheet(css_file: Path) -> str:
    if css_file.is_file():
        with open(css_file) as f:
            return f.read()
    return ""


def install_fonts():
    global FONTS_INSTALLED
    if FONTS_INSTALLED:
        return

    for child in FONTS_DIR.iterdir():
        if str(child).endswith(".ttf"):
            QtGui.QFontDatabase.addApplicationFont(str(child))

    FONTS_INSTALLED = True


FONTS_INSTALLED = False

GUI_DIR = Path(__file__).parent
FONTS_DIR = GUI_DIR / "fonts"
CSS_DIR = GUI_DIR / "css"
BASE_CSS = _load_stylesheet(CSS_DIR / "base.css")
ITEM_CSS = _load_stylesheet(CSS_DIR / "item.css")
LIST_CSS = _load_stylesheet(CSS_DIR / "list.css")
HEADER_CSS = _load_stylesheet(CSS_DIR / "header.css")
