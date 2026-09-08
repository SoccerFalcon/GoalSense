from pathlib import Path
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app_controller import AppController

PROJECT_ROOT = Path(__file__).resolve().parent
APP_ICON_PATH = PROJECT_ROOT / "Assets" / "Icon.png"

def main():
  app = QApplication(sys.argv)
  app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
  app.setApplicationName("Soccer Goal Prediction")
  controller = AppController()

  sys.exit(app.exec())

if __name__ == "__main__":
  main()