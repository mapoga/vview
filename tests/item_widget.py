import random
import os
import datetime
import sys

from PySide2 import QtGui, QtWidgets

import vview.gui.widgets.version_widget

app = QtWidgets.QApplication(sys.argv)

# Fonts
fonts_dir = "/home/mapoga/Documents/python/vview/vview/gui/fonts"
for filename in os.listdir(fonts_dir):
    if filename.endswith(".ttf"):
        QtGui.QFontDatabase.addApplicationFont(os.path.join(fonts_dir, filename))

# thumbnails
thumb_dir = "/home/mapoga/Documents/python/vview/tests/image_samples/thumbnails"
thumb_paths = []
for filename in os.listdir(thumb_dir):
    thumb_paths.append(os.path.join(thumb_dir, filename))

thumb_path = random.choice(thumb_paths)
print("thumb_path", thumb_path)
thumbnail = QtGui.QPixmap(thumb_path)

widget = vview.gui.widgets.version_widget.VersionWidget(
    name="v001",
    path="/home/mapoga/Documents/python/vview/vview/gui/widgets/manager.py",
    frames="1001-1060",
    timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    # thumbnail=thumbnail,
)

widget._set_selected(True)

widget.show()
app.exec_()
