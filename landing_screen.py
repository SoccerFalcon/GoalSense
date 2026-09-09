from math import cos, sin

from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

# Window that shows on startup
class LandingScreen(QWidget):
    DEFAULT_WINDOW_WIDTH: int = 960
    DEFAULT_WINDOW_HEIGHT: int = 540
    MIN_WINDOW_WIDTH: int = 520
    MIN_WINDOW_HEIGHT: int = 380

    FPS: int = 24

    HORIZONTAL_MARGIN: int = 50
    TOP_MARGIN: int = 30
    BOTTOM_MARGIN: int = 30
    LAYOUT_SPACING: int = 18

    select_region_clicked: pyqtSignal = pyqtSignal()
    
    def __init__(self):
        super().__init__()

        # Set sizing and basic appearance
        self.resize(self.DEFAULT_WINDOW_WIDTH, self.DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(self.MIN_WINDOW_WIDTH, self.MIN_WINDOW_HEIGHT)
        self.background_color: str = "#0D1527"

        # Background animation set up
        self.animation_phase: float = 0.0
        self.animation_timer: QTimer = QTimer(self)
        self.animation_timer.setInterval(1000 // self.FPS)
        self.animation_timer.timeout.connect(self.advance_background)

        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self.HORIZONTAL_MARGIN,
            self.TOP_MARGIN,
            self.HORIZONTAL_MARGIN,
            self.BOTTOM_MARGIN
        )
        layout.setSpacing(self.LAYOUT_SPACING)

        self.title_label = QLabel("GoalSense: Real-Time Threat Prediction for Soccer", self)
        self.title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: white;"
            "font-family: Segoe UI, sans-serif;"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.select_region_button = QPushButton("Select Region", self)
        self.select_region_button.setStyleSheet(
            """
            QPushButton {
                background-color: #22C55E;
                color: black;
                border: 1px solid white;
                border-radius: 5px;
                padding: 10px;
                font-size: 18px;
                font-family: Segoe UI, sans-serif;
                max-width: 200px;
              }
            """
        )
        self.select_region_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.select_region_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.select_region_button.clicked.connect(self.on_select_region_clicked)

    def on_select_region_clicked(self):
        self.hide()
        QTimer.singleShot(500, self.select_region_clicked.emit)  # Emit the signal after a short delay to ensure the window is hidden

    def advance_background(self):
        self.animation_phase += 1 / self.FPS
        self.update()

    def showEvent(self, event):
        self.animation_timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.animation_timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width: int = self.width()
        height: int = self.height()

        # Linear gradient in very back
        background: QLinearGradient = QLinearGradient(0, 0, width, height)
        background.setColorAt(0, QColor("#14233d"))
        background.setColorAt(0.5, QColor("#0d1527"))
        background.setColorAt(1, QColor("#07111f"))
        painter.fillRect(self.rect(), background)

        # Circular gradients that move in the background.
        # Each circle is represents by x and y normalized
        # coordinates and a radius in pixels
        circles: tuple[tuple[float, float, int], ...] = (
            (0.15, 0.2, 250),
            (0.8, 0.3, 220),
            (0.5, 0.9, 280)
        )
        path_circle_radius: float = 0.035  # The radius of the circle that the circular gradients
                                           # move in. Represented by a normalized value.

        for index, (base_x, base_y, radius) in enumerate(circles):
            x: float = width * (base_x + path_circle_radius * cos(self.animation_phase + index))
            y: float = height * (base_y + path_circle_radius * sin(self.animation_phase + index))
            glow = QRadialGradient(x, y, radius)
            glow.setColorAt(0, QColor(34, 197, 94, 24))
            glow.setColorAt(1, QColor(34, 197, 94, 0))
            painter.fillRect(self.rect(), glow)

        # Draw soccer field
        field_width = width * 0.80
        field_height = height * 0.75
        field_left = (width - field_width) / 2
        field_top = (height - field_height) / 2
        painter.setPen(QPen(QColor(226, 232, 240, 24), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Border
        painter.drawRect(
            int(field_left), int(field_top), int(field_width), int(field_height)
        )

        # Halfway line
        painter.drawLine(
            int(width / 2), int(field_top), int(width / 2), int(field_top + field_height)
        )

        # Center circle
        circle_radius = min(field_width, field_height) * 0.15
        painter.drawEllipse(
            int(width / 2 - circle_radius),
            int(height / 2 - circle_radius),
            int(circle_radius * 2),
            int(circle_radius * 2),
        )

        # Player markers.
        # First two elements are normalized x and y coords,
        # third element is animation offset.
        marker_positions: tuple[tuple[float, float, float], ...] = (
            (0.27, 0.30, 0.0),
            (0.40, 0.63, 1.2),
            (0.60, 0.37, 2.3),
            (0.74, 0.68, 3.4),
        )

        # Radius for the motion of the players
        player_motion_radius: float = 0.025
        # Radius for the dots representing players
        player_circle_diam: int = 10

        # Draw the players
        for x_fraction, y_fraction, offset in marker_positions:
            x: int = field_left + field_width * (
                x_fraction + player_motion_radius * sin(self.animation_phase + offset)
            )
            y: int = field_top + field_height * (
                y_fraction + player_motion_radius * cos(self.animation_phase + offset)
            )
            painter.setBrush(QColor(74, 222, 128, 58))
            painter.setPen(QPen(QColor(134, 239, 172, 90), 1))
            painter.drawEllipse(
                int(x - player_circle_diam // 2),
                int(y - player_circle_diam // 2),
                player_circle_diam,
                player_circle_diam
            )

        painter.end()
