from pathlib import Path
import random
import datetime
import sys

from PySide2 import QtGui, QtWidgets

import vview.gui.widgets.item_widget


def get_test_tumbnails():
    result = []
    test_dir = Path(__file__).absolute().parent
    thumb_dir = test_dir / "image_samples" / "thumbnails"

    for child in thumb_dir.iterdir():
        if child.is_file():
            result.append(str(child))
    return result


app = QtWidgets.QApplication(sys.argv)

thumb_paths = get_test_tumbnails()
thumb_path = random.choice(thumb_paths)
print("thumb_path", thumb_path)
thumbnail = QtGui.QPixmap(thumb_path)

widget = vview.gui.widgets.item_widget.VersionItemWidget(
    name="v001",
    path="/home/mapoga/Documents/python/vview/vview/gui/widgets/manager.py",
    frames="1001-1060",
    date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    # thumbnail=thumbnail,
)

widget._set_selected(True)

widget.show()
app.exec_()
