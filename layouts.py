from PyQt6.QtWidgets import QLayout, QSizePolicy
from PyQt6.QtCore import Qt, QPoint, QRect, QSize

class QFlowLayout(QLayout):
    def __init__(self, parent=None, margin=10, h_spacing=5, v_spacing=5):
        super(QFlowLayout, self).__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.item_list.append(item)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super(QFlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margin, _, _, _ = self.getContentsMargins()
        size += QSize(2 * margin, 2 * margin)
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        for item in self.item_list:
            wid = item.widget()
            space_x = self._h_spacing
            if space_x == -1:
                space_x = wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton,
                                                    QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal)
            space_y = self._v_spacing
            if space_y == -1:
                space_y = wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton,
                                                    QSizePolicy.ControlType.PushButton, Qt.Orientation.Vertical)

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y()