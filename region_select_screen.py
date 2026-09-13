from PyQt6.QtCore import pyqtSignal, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QScreen
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

class RegionSelectScreen(QWidget):
  region_selected: pyqtSignal = pyqtSignal(int, int, int, int)  # x, y, width, height

  def __init__(self):
    super().__init__()
    self.start_x: int = 0
    self.start_y: int = 0
    self.end_x: int = 0
    self.end_y: int = 0

    self.is_drawing: bool = False

    self.setCursor(Qt.CursorShape.CrossCursor)

    self.confirm_button: CustomButton = CustomButton("Confirm", self)
    self.confirm_button.set_active(False)
    
    self.confirm_button.clicked.connect(self.on_confirm)

    self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

  # Before this window becomes visible, grab the user's current screen to know what is
  # underneath this window
  def showEvent(self, event):
    self.underneath = QApplication.primaryScreen().grabWindow(0)
    self.screen: QScreen = QApplication.primaryScreen()
    self.dpr: float = self.screen.devicePixelRatio()

  # When the user presses down the mouse, start drawing the rectangle
  def mousePressEvent(self, event):
    if event.button() != Qt.MouseButton.LeftButton:
      return
    
    self.is_drawing = True

    self.start_x = event.globalPosition().toPoint().x()
    self.start_y = event.globalPosition().toPoint().y()
    self.end_x = self.start_x
    self.end_y = self.start_y

    self.update()

  # While the user moves the mouse while holding down the left mouse button,
  # update the rectangle
  def mouseMoveEvent(self, event):
    if not self.is_drawing:
      return
    
    self.end_x = event.globalPosition().toPoint().x()
    self.end_y = event.globalPosition().toPoint().y()
    self.update()

  # When the user releases the mouse, stop updating the rectangle
  def mouseReleaseEvent(self, event):
    if event.button() != Qt.MouseButton.LeftButton or not self.is_drawing:
      return
    
    self.is_drawing = False
    self.confirm_button.set_active(self.end_x != self.start_x and
                                   self.end_y != self.start_y)
    self.update()
    
  # When the user confirms the region, change screen
  def on_confirm(self):
    self.hide()
    self.region_selected.emit(
      int(min(self.start_x, self.end_x) * self.dpr),
      int(min(self.start_y, self.end_y) * self.dpr),
      int(abs(self.end_x - self.start_x) * self.dpr),
      int(abs(self.end_y - self.start_y) * self.dpr)
    )

  def paintEvent(self, event): 
    painter: QPainter = QPainter(self)

    # Draw what is underneath this window, then a semi-transparent
    # rectangle above it to give the illusion of semi-transparency
    painter.drawPixmap(self.rect(), self.underneath)
    painter.fillRect(
      self.rect(),
      QColor(0, 0, 0, 180)
    )

    if self.start_x == self.end_x or self.start_y == self.end_y:
      painter.end()
      return

    x: int = min(self.start_x, self.end_x)
    y: int = min(self.start_y, self.end_y)
    width: int = abs(self.end_x - self.start_x)
    height: int = abs(self.end_y - self.start_y)
    selection_rect: QRect = QRect(x, y, width, height)

    # Draw what is underneath this window in the region that the user selected to
    # give the illusion of a hole where the user defined
    painter.drawPixmap(
      selection_rect,
      self.underneath,
      QRect(
        int(x * self.underneath.width()/self.width()),
        int(y * self.underneath.height()/self.height()),
        int(width * self.underneath.width()/self.width()),
        int(height * self.underneath.height()/self.height())
      )
    )
    painter.setPen(QPen(QColor(255, 255, 255), 2))
    painter.drawRect(selection_rect)
    painter.end()
  
  def resizeEvent(self, event):
    margin: int = 20
    button_width: int = 100
    button_height: int = 40

    self.confirm_button.setGeometry(
      self.width() - button_width - margin,
      self.height() - button_height - margin,
      button_width,
      button_height
    )

    super().resizeEvent(event)

# Custom button class to allow for custom cursor and tooltip when hovered over
# even while disabled
class CustomButton(QPushButton):
  def __init__(self, text, parent):
    super().__init__(text, parent)
    self.active: bool = None
    self.set_active(False)

  def set_active(self, is_active: bool):
    self.active = is_active
    if self.active:
      self.setCursor(Qt.CursorShape.PointingHandCursor)
      self.setToolTip("")
      self.setStyleSheet(
        """
        QPushButton {
          background-color: white;
          color: black;
          border: 1px solid black;
          border-radius: 5px;
          padding: 5px;
        }

        QPushButton:hover {
          background-color: #dddddd;
        }
        """
      )
    else:
      self.setCursor(Qt.CursorShape.ForbiddenCursor)
      self.setToolTip("Please select a region of your screen")
      self.setStyleSheet(
        """ 
        QPushButton {
          background-color: #aaaaaa;
          color: #666666;
        }

        QToolTip {
          background-color: white;
          color: black;
        }
        """
      )

  def mousePressEvent(self, e):
    if self.active:
      return super().mousePressEvent(e)

  