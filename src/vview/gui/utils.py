from enum import Enum
from PySide2 import QtCore, QtGui, QtSvg


class ReformatType(Enum):
    """Types of QPixmap reformat

    Attributes:
        FIT:        Uniform scale to fit inside the available space.
                    May leave some empty space.
        FILL:       Uniform scale to fill ALL the available space.
                    Will never leave empty space.
        DISTORT:    Anamorphic scale to fill ALL the available space.
                    Will never leave empty space.
        EXPANDING:  Uniform scale to match the available height.
                    The width is unbound in this mode and may be smaller or bigger.
    """

    FIT = 0
    FILL = 1
    DISTORT = 2
    EXPANDING = 3


def svg_to_pixmap(
    svg_file: str,
    size: QtCore.QSize,
    scale: QtCore.QSizeF,
    fg_color: QtGui.QColor,
    bg_color: QtGui.QColor,
) -> QtGui.QPixmap:
    """Convert an SVG to QPixmap and override the colors

    Args:
        svg_file:   SVG file to convert.
        size:       Size of the QPixmap.
        bg_color:   Color of the background.
        fg_color:   Color of the foreground. The SVG colors are not preserved.
        scale:      Scale the SVG inside the bounds of the QPixmap.
    """
    # Backgound
    pixmap = QtGui.QPixmap(size)
    pixmap.fill(bg_color)
    painter = QtGui.QPainter(pixmap)

    # Render Region
    region = QtCore.QRectF(
        0, 0, scale.width() * size.height(), scale.height() * size.height()
    )
    center = QtCore.QRectF(pixmap.rect()).center()
    # center = pixmap.rect().toRectF().center()
    region.moveCenter(center)

    # Svg
    svg_renderer = QtSvg.QSvgRenderer(svg_file)
    svg_renderer.render(painter, region)
    painter.setCompositionMode(painter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), fg_color)
    painter.end()

    return pixmap


def reformat(
    pixmap: QtGui.QPixmap,
    size: QtCore.QSize,
    reformat_type: ReformatType,
    transform_mode: QtCore.Qt.TransformationMode = QtCore.Qt.SmoothTransformation,
    bg_color: QtGui.QColor = QtGui.QColor(0, 0, 0, 1),
) -> QtGui.QPixmap:
    """Return a reformatted copy of the QPixmap

    Args:
        pixmap:         Original QPixmap to reformat.
        size:           Size to refornat to.
        reformat_type:  Type of reformat to execute.
        bg_color:       Color of the background.
                        Only used for type ReformatType.FIT
    """
    p_ratio = float(pixmap.width()) / float(pixmap.height())
    s_ratio = float(size.width()) / float(size.height())

    if reformat_type == ReformatType.FIT:
        # First make smaller than the size
        pix = pixmap.scaled(size, QtCore.Qt.KeepAspectRatio, transform_mode)

        # Define a region within the size
        rect = pix.rect()
        size_rect = QtCore.QRect(0, 0, size.width(), size.height())
        rect.moveCenter(size_rect.center())

        # Paint the region
        result = QtGui.QPixmap(size)
        result.fill(bg_color)
        painter = QtGui.QPainter(result)
        painter.drawPixmap(rect, pix)
        return result

    elif reformat_type == ReformatType.FILL:
        # First overflow
        if p_ratio > s_ratio:
            pix = pixmap.scaledToHeight(size.height(), transform_mode)
        else:
            pix = pixmap.scaledToWidth(size.width(), transform_mode)

        # Then crop
        rect = QtCore.QRect(0, 0, size.width(), size.height())
        rect.moveCenter(pix.rect().center())
        return pix.copy(rect)

    elif reformat_type == ReformatType.DISTORT:
        return pixmap.scaled(size, QtCore.Qt.IgnoreAspectRatio, transform_mode)

    elif reformat_type == ReformatType.EXPANDING:
        return pixmap.scaledToHeight(size.height(), transform_mode)
