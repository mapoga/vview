from typing import List, Tuple

from PySide2 import QtCore, QtGui, QtWidgets

import vview.gui.style

from .item_widget import VersionWidget


class VersionListWidget(QtWidgets.QListWidget):
    UNIFORM_HEIGHT = 56

    def __init__(
        self,
        max_visible_items: int = 5,
        scrollbar_enabled: bool = True,
        parent=None,
    ):
        super(VersionListWidget, self).__init__(parent)
        vview.gui.style.install_fonts()

        self._max_visible_items = max_visible_items
        self._scrollbar_enabled = scrollbar_enabled

        self._init_ui()
        self._init_connects()
        self._init_actions()

        self.set_max_visible_items(max_visible_items)
        self.set_scrollbar_enabled(scrollbar_enabled)

    # Settings ---------------------------------------------------------------
    def max_visible_items(self) -> int:
        return self._max_visible_items

    def set_max_visible_items(self, max_visible_items: int):
        self._max_visible_items = max_visible_items
        self._refresh_ui()

    def scrollbar_enabled(self) -> bool:
        return self._scrollbar_enabled

    def set_scrollbar_enabled(self, is_enabled: bool):
        self._scrollbar_enabled = is_enabled
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAsNeeded if is_enabled else QtCore.Qt.ScrollBarAlwaysOff
        )
        self._refresh_ui()

    # Items ------------------------------------------------------------------
    def add_version(self, widget: VersionWidget) -> QtWidgets.QListWidgetItem:
        item = QtWidgets.QListWidgetItem()
        self.insertItem(0, item)
        self.setItemWidget(item, widget)
        self._update_item_size_hint(item)
        return item

    # Selection --------------------------------------------------------------
    def selected_index(self) -> int:
        model = self.selectionModel()
        if model is not None:
            for model_idx in model.selectedIndexes():
                idx = model_idx.row()
                if isinstance(idx, int):
                    return idx
        return -1

    def set_selected_index(self, idx: int):
        model = self.model()
        if model is not None:
            model_idx = model.index(idx, 0)
            if model_idx is not None:
                selection_model = self.selectionModel()
                if selection_model is not None:
                    selection_model.setCurrentIndex(
                        model_idx, QtCore.QItemSelectionModel.ClearAndSelect
                    )

    def select_next(self) -> int:
        idx = self.selected_index()
        if idx >= 0:
            idx = max(idx - 1, 0)
            self.set_selected_index(idx)
            return idx
        else:
            return self.select_last()

    def select_prev(self) -> int:
        idx = self.selected_index()

        if idx >= 0:
            idx = min(idx + 1, self.count() - 1)
            self.set_selected_index(idx)
            return idx
        else:
            return self.select_first()

    def select_last(self) -> int:
        if self.count() > 0:
            self.set_selected_index(0)
            return 0
        else:
            return -1

    def select_first(self) -> int:
        if self.count() > 0:
            idx = self.count() - 1
            self.set_selected_index(idx)
            return idx
        else:
            return -1

    # Re-Implemented methods -------------------------------------------------
    def sizeHint(self) -> QtCore.QSize:
        size_hint = super(VersionListWidget, self).sizeHint()

        height = self._height_for_max_items(
            self.max_visible_items(), self.UNIFORM_HEIGHT
        )
        size_hint.setHeight(height)
        return size_hint

    def resizeEvent(self, e):
        super(VersionListWidget, self).resizeEvent(e)
        self._update_items_size_hint()

    # Private ----------------------------------------------------------------
    def _init_ui(self):
        self.setStyleSheet(vview.gui.style.BASE_CSS + vview.gui.style.LIST_CSS)
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(), QtWidgets.QSizePolicy.Fixed
        )
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setUniformItemSizes(True)

    def _init_connects(self):
        self.itemSelectionChanged.connect(self._on_items_selection_changed)

    def _init_actions(self):
        # prev / next
        right_arrow_act = QtWidgets.QAction("next", parent=self)
        right_arrow_act.setShortcut(QtGui.QKeySequence("right"))
        right_arrow_act.triggered.connect(self.select_next)
        self.addAction(right_arrow_act)

        left_arrow_act = QtWidgets.QAction("prev", parent=self)
        left_arrow_act.setShortcut(QtGui.QKeySequence("left"))
        left_arrow_act.triggered.connect(self.select_prev)
        self.addAction(left_arrow_act)

        # min / max
        min_act = QtWidgets.QAction("min", parent=self)
        min_act.setShortcuts(
            [
                QtGui.QKeySequence("Ctrl+down"),
                QtGui.QKeySequence("Ctrl+left"),
            ]
        )
        min_act.triggered.connect(self.select_first)
        self.addAction(min_act)

        max_act = QtWidgets.QAction("max", parent=self)
        max_act.setShortcuts(
            [
                QtGui.QKeySequence("Ctrl+up"),
                QtGui.QKeySequence("Ctrl+right"),
            ]
        )
        max_act.triggered.connect(self.select_last)
        self.addAction(max_act)

    # Event Callbacks --------------------------------------------------------
    def _on_items_selection_changed(self):
        self._update_items_state()
        self._center_selected_item()

    # Helpers ----------------------------------------------------------------
    def _refresh_ui(self):
        self.style().unpolish(self)
        self.style().polish(self)

    def _height_for_max_items(self, max_count: int, items_uniform_height: int) -> int:
        true_count = min(self.count(), max_count)

        # Items height
        height = true_count * items_uniform_height

        # Spacing (including ends)
        height += (true_count + 1) * self.spacing()

        # Margins
        margins = self.contentsMargins()
        height += margins.top() + margins.bottom()
        return height

    def _update_items_state(self):
        for item, widget in self._item_widget_tuples():
            widget._set_selected(item.isSelected())

    def _center_selected_item(self):
        selected_indexes = self.selectedIndexes()
        if selected_indexes:
            self.scrollTo(
                selected_indexes[0], QtWidgets.QAbstractItemView.PositionAtCenter
            )

    def _update_items_size_hint(self):
        for item, _ in self._item_widget_tuples():
            self._update_item_size_hint(item)

    def _update_item_size_hint(self, list_widget_item):
        viewport = self.viewport()
        if viewport is not None:
            size_hint = QtCore.QSize(viewport.size().width(), self.UNIFORM_HEIGHT)
            list_widget_item.setSizeHint(size_hint)

    def _item_widget_tuples(
        self,
    ) -> List[Tuple[QtWidgets.QListWidgetItem, VersionWidget]]:
        result = []
        count = self.count()
        for i in range(count):
            item = self.item(i)
            if item:
                widget = self.itemWidget(item)
                if widget:
                    if isinstance(widget, VersionWidget):
                        result.append((item, widget))
        return result
