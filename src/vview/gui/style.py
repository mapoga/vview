import os
from PySide2 import QtGui


def _load_stylesheet(css_file: str) -> str:
    if os.path.exists(css_file):
        with open(css_file) as f:
            return f.read()
    return ""


def install_fonts():
    global FONTS_INSTALLED
    if FONTS_INSTALLED:
        return

    fonts_dir = os.path.join(GUI_DIR, "fonts")

    for name in os.listdir(fonts_dir):
        if name.endswith(".ttf"):
            font_file = os.path.join(fonts_dir, name)
            QtGui.QFontDatabase.addApplicationFont(font_file)

    FONTS_INSTALLED = True


FONTS_INSTALLED = False

GUI_DIR = os.path.dirname(__file__)
BASE_CSS = _load_stylesheet(os.path.join(GUI_DIR, "css", "base.css"))
ITEM_CSS = _load_stylesheet(os.path.join(GUI_DIR, "css", "item.css"))
LIST_CSS = _load_stylesheet(os.path.join(GUI_DIR, "css", "list.css"))
HEADER_CSS = _load_stylesheet(os.path.join(GUI_DIR, "css", "header.css"))
ICONS_DIR = os.path.join(GUI_DIR, "icons")
