from collections import deque

from PyQt6.QtCore import pyqtSignal, Qt, QThread, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from model import load_model
from worker import CaptureWorker

class PredictionScreen(QMainWindow):
  redefine_requested: pyqtSignal = pyqtSignal()

  def __init__(self, region_selector):
    super().__init__()

    region_selector.region_selected.connect(self.update_selected_region)

    self.setWindowTitle("Prediction Screen")
    self.resize(500, 300)

    self.model, self.device = load_model()

    self.capture_thread = None
    self.worker = None

    self.pending_region = None
    self.is_closing = False

    centralWidget = QWidget()
    self.setCentralWidget(centralWidget)

    layout = QVBoxLayout(centralWidget)

    self.probability_label = QLabel("-")
    self.probability_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    self.description_label = QLabel("GOAL PROBABILITY")
    self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    self.probability_graph_scene = QGraphicsScene()
    self.probability_graph_view = QGraphicsView(self.probability_graph_scene)
    self.probability_graph_view.setRenderHint(QPainter.RenderHint.Antialiasing)
    self.probability_graph_view.setHorizontalScrollBarPolicy(
      Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    self.probability_graph_view.setVerticalScrollBarPolicy(
      Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )

    self.redefine_button = QPushButton("Redefine Region")
    self.redefine_button.clicked.connect(self.request_redefine)

    layout.addWidget(self.description_label)
    layout.addWidget(self.probability_label)
    layout.addWidget(self.probability_graph_view)
    layout.addWidget(self.redefine_button)

    self.probabilities = deque(maxlen = 100)
    self.graph_margin = 12

  def resizeEvent(self, event):
    super().resizeEvent(event)
    QTimer.singleShot(0, self.sync_graph_scene_to_view)

  def showEvent(self, event):
    super().showEvent(event)
    QTimer.singleShot(0, self.sync_graph_scene_to_view)

  def sync_graph_scene_to_view(self):
    viewport = self.probability_graph_view.viewport()
    self.probability_graph_scene.setSceneRect(
      0,
      0,
      viewport.width(),
      viewport.height(),
    )
    self.update_graph()

  def new_probability(self, probability):
    self.probability_label.setText(f"{probability: 0.1%} chance of a goal")
    self.probabilities.append(probability)
    self.update_graph()

  def update_graph(self):
    if len(self.probabilities) < 2:
      return
    
    self.probability_graph_scene.clear()

    width = self.probability_graph_scene.width()
    height = self.probability_graph_scene.height()
    if width <= 0 or height <= 0:
      return

    left = self.graph_margin
    right = width - self.graph_margin
    top = self.graph_margin
    bottom = height - self.graph_margin
    plot_width = right - left
    plot_height = bottom - top

    spacing = plot_width / (self.probabilities.maxlen - 1)

    last_color = None
    color_coeff = 5

    # Create the lines for each pair of adjacent points
    # Each line has a color based on its slope
    for i in range(len(self.probabilities)-1, 0, -1):
      x1 = right - ((len(self.probabilities) - 1 - i) * spacing)
      y1 = bottom - (plot_height * self.probabilities[i])
      x2 = right - ((len(self.probabilities) - i) * spacing)
      y2 = bottom - (plot_height * self.probabilities[i - 1])

      line_item = self.probability_graph_scene.addLine(x1, y1, x2, y2)

      slope = -(y2 - y1) / (x2 - x1) if x2 != x1 else 0
      red = int(min(max(0, 200 - color_coeff * slope ), 255))
      green = int(min(max(0, 200 + color_coeff * slope), 255))
      last_color = QColor(red, green, 0)
      line_item.setPen(QPen(last_color, 2))

    # Create the circle at the latest proability point
    latest_y = bottom - (plot_height * self.probabilities[-1])
    circle = self.probability_graph_scene.addEllipse(right-5, latest_y-5, 10, 10)
    circle.setPen(QPen(last_color, 2))

  # When a new region is defined by the user, stop the current thread and
  # start a new one
  def update_selected_region(self, x, y, width, height):
    region = (x, y, width, height)
    # If there already is an existing thread, make this region pending instead
    # of immediately overwriting it, and wait for the current thread to finish
    if self.capture_thread is not None:
      self.pending_region = region
      if self.capture_thread.isRunning():
        self.capture_thread.requestInterruption()
    else:
      self.start_capture_worker(*region)

  def start_capture_worker(self, x, y, width, height):
    self.capture_thread = QThread(self)
    self.worker = CaptureWorker(x, y, width, height, self.model, self.device)
    self.worker.moveToThread(self.capture_thread)

    self.capture_thread.started.connect(self.worker.run)
    self.worker.prediction_ready.connect(self.new_probability)
    self.worker.error_occurred.connect(self.handle_error)

    self.worker.finished.connect(self.capture_thread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.capture_thread.finished.connect(self.capture_thread.deleteLater)
    self.capture_thread.finished.connect(self.on_worker_thread_finished)

    self.capture_thread.start()

  def request_redefine(self):
    if self.capture_thread is not None:
      self.capture_thread.requestInterruption()

    self.hide()
    QTimer.singleShot(500, self.redefine_requested.emit)

  def on_worker_thread_finished(self):
    self.worker = None
    self.capture_thread = None

    # If the app is being closed, close the app
    if self.is_closing:
      self.close()
      return

    # If there is a pending region, make a new worker for it
    if self.pending_region is not None:
      region = self.pending_region
      self.pending_region = None
      self.start_capture_worker(*region)

  def handle_error(self, error_message):
    print(error_message)
    self.probability_label.setText(f"Error: {error_message}")

  def closeEvent(self, event):
    if self.capture_thread is not None and self.capture_thread.isRunning():
      self.is_closing = True
      self.capture_thread.requestInterruption()
      event.ignore()
      return

    event.accept()

