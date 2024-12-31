from pathlib import Path
import random
import datetime
import sys

from PySide2 import QtCore, QtWidgets, QtGui

from vview.gui import VersionItemWidget, VersionDialog


def get_test_tumbnails():
    result = []
    test_dir = Path(__file__).absolute().parent
    thumb_dir = test_dir / "image_samples" / "thumbnails"

    for child in thumb_dir.iterdir():
        if child.is_file():
            result.append(str(child))
    return result


def main():
    app = QtWidgets.QApplication(sys.argv)
    version_dialog = VersionDialog()

    thumb_paths = get_test_tumbnails()
    total_count = random.choice(range(5, 20))
    print(f"{thumb_paths}, {total_count}")
    widgets = []

    for i in range(1, total_count + 1):
        path = random.choice(thumb_paths)

        # Create widget
        version_widget = VersionItemWidget(
            name="v{:03}".format(i),
            path=path,
            frames="1001-1060",
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            # thumb_width=200,
        )
        version_dialog.list_widget.add_version(version_widget)
        widgets.append(version_widget)

        version_widget.set_thumb_enabled(True)

        # # Add thumbnail
        # pixmap = QtGui.QPixmap(path)
        # if i % 2 == 1:
        #     version_widget.set_thumb_pixmap(pixmap)

        # # Generate thumbnail
        # def add_tumb_pixmap(output):
        #     filepath = Path(output)
        #     if filepath.is_file():
        #         pixmap = QtGui.QPixmap.fromImage(output)
        #         version_widget.set_thumb_enabled(True)
        #         version_widget.set_thumb_pixmap(pixmap)
        #
        # vview.core.thumb.temp_cache.get_create(
        #     source=path,
        #     callback=add_tumb_pixmap,
        # )

    # # Mess things up
    # v_list_widget.set_selected_index(2)
    # timer = QtCore.QTimer()
    # timer.timeout.connect(lambda: v_list_widget.select_prev())
    # timer.start(1000)

    # Populate thumbnails
    def callback():
        for w in widgets:
            if w.thumb_pixmap() is None:
                path = random.choice(thumb_paths)
                # path = thumb_paths[0]
                pixmap = QtGui.QPixmap(path)
                w.set_thumb_pixmap(pixmap)
                return

    t_timer = QtCore.QTimer()
    t_timer.timeout.connect(callback)
    t_timer.start(400)

    # Show
    version_dialog.list_widget.select_last()
    version_dialog.adjustSize()
    size = version_dialog.size()
    version_dialog.resize(700, size.height())
    version_dialog.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
