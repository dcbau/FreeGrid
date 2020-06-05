import sys
from PyQt5.QtWidgets import QAbstractButton
from PyQt5.QtGui import QPainter

class PicButton(QAbstractButton):
    def __init__(self, pixmap, pixmap_mouseover, pixmap_pressed, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap
        self.pixmap_mouseover = pixmap_mouseover
        self.pixmap_pressed = pixmap_pressed
        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        pix = self.pixmap_mouseover if self.underMouse() else self.pixmap
        if self.isDown():
            pix = self.pixmap_pressed

        painter.drawPixmap(event.rect(), pix)

    def sizeHint(self):
        return self.pixmap.size()

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

