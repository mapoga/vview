from PySide2 import QtCore, QtGui, QtWidgets


class ElidedLabel(QtWidgets.QLabel):
    pressed = QtCore.Signal()

    def __init__(self, elideMode=QtCore.Qt.ElideRight, *args, **kwargs):
        """Clickable elided QLabel

        Useful for displaying a long path on a single line
        """
        super(ElidedLabel, self).__init__(*args, **kwargs)
        self._elideMode = elideMode
        self._hoverColor = QtGui.QColor()
        self.setMouseTracking(True)

    # Public -----------------------------------------------------------------
    def elideMode(self) -> QtCore.Qt.TextElideMode:
        return self._elideMode

    def setElideMode(self, mode: QtCore.Qt.TextElideMode):
        # Workaround
        # Could not find a way to use colors from the stylesheet
        self._elideMode = mode
        if mode != self.elideMode():
            self.updateGeometry()

    def hoverColor(self) -> QtGui.QColor:
        return self._hoverColor

    def setHoverColor(self, color: QtGui.QColor):
        self._hoverColor = color
        if color != self.hoverColor():
            self.updateGeometry()

    # Private ----------------------------------------------------------------
    def _totalMargins(self):
        return self.contentsMargins() + QtCore.QMargins(
            self.margin(), self.margin(), self.margin(), self.margin()
        )

    # Re-implemented methods -------------------------------------------------
    def minimumSizeHint(self) -> QtCore.QSize:
        size = super(ElidedLabel, self).minimumSizeHint()
        size.setWidth(12)
        return size

    def paintEvent(self, event):
        opt = QtWidgets.QStyleOptionFrame()
        opt.initFrom(self)
        p = QtGui.QPainter(self)
        s = self.style()

        # Hover color
        if QtWidgets.QStyle.State_MouseOver & opt.state:
            if self.hoverColor().isValid():
                opt.palette.setColor(QtGui.QPalette.Text, self.hoverColor())

        # Area
        rect = event.rect()
        margins = self._totalMargins()
        rect = rect.marginsRemoved(margins)

        # Edlided Text
        txt = self.fontMetrics().elidedText(self.text(), self.elideMode(), rect.width())

        s.drawItemText(
            p,
            rect,
            self.alignment(),
            opt.palette,
            self.isEnabled(),
            txt,
            QtGui.QPalette.Text,
        )

    def enterEvent(self, event):
        super(ElidedLabel, self).enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super(ElidedLabel, self).leaveEvent(event)
        self.update()

    def mousePressEvent(self, ev):
        super(ElidedLabel, self).mousePressEvent(ev)
        self.pressed.emit()
