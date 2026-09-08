from collections import deque
import time

import mss
import numpy as np
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject, QThread
import torch

from model import predict

class CaptureWorker(QObject):
  prediction_ready = pyqtSignal(float) # confidence of goal
  finished = pyqtSignal()
  error_occurred = pyqtSignal(str)
    
  def __init__(self, x, y, width, height, model, device):
    super().__init__()
    self.frame_buffer = deque()
    self.region = {"top": y, "left": x, "width": width, "height": height}
    self.model = model
    self.device = device

  @pyqtSlot()
  def run(self):
    try:
      with mss.mss() as sct:
        while not QThread.currentThread().isInterruptionRequested():
          # Grab the frame and add to buffer
          screenshot = sct.grab(self.region)
          self.frame_buffer.append((np.array(screenshot)[:,:,:-1][:,:,::-1], time.time()))

          # Trim the buffer to keep only the last 3 seconds of frames
          while self.frame_buffer[-1][1] - self.frame_buffer[0][1] > 3:
            self.frame_buffer.popleft()

          # If there are enough frames in the buffer run inference
          if len(self.frame_buffer) >= 16:
            indices = np.linspace(0, len(self.frame_buffer) - 1, num=16, dtype=int)
            frames = [torch.from_numpy(self.frame_buffer[i][0].copy()).permute(2, 0, 1) for i in indices]
            self.prediction_ready.emit(predict(self.model, torch.stack(frames, dim=1), self.device))

          time.sleep(1/15) # Capture at most 15 fps
    except Exception as e:
      self.error_occurred.emit(str(e))
    finally:
      self.finished.emit()

