from landing_screen import LandingScreen
from prediction_screen import PredictionScreen
from region_select_screen import RegionSelectScreen

# Windowsless class that coordinates the different states and windows
# of the app
class AppController:
  def __init__(self):
    self.landing_screen: LandingScreen = LandingScreen()  # Screen that shows on startup
    self.region_select_screen: RegionSelectScreen = RegionSelectScreen()  # Screen to select a region of the screen
    self.prediction_screen: PredictionScreen = PredictionScreen(self.region_select_screen)  # Window that shows prediction overlay

    self.landing_screen.select_region_clicked.connect(self.show_region_selection)
    self.region_select_screen.region_selected.connect(self.show_prediction)
    self.prediction_screen.redefine_requested.connect(self.show_region_selection)

    self.landing_screen.show()

  def show_region_selection(self) -> None:
    self.region_select_screen.showFullScreen()

  def show_prediction(self, _x, _y, _width, _height) -> None:
    self.prediction_screen.show()