import sys
from numpy import arange, sin, array
from PySide.QtCore import *
from PySide.QtGui import *

app = QApplication(sys.argv)

from enthought.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = "qt4"
from enthought.enable.api import Window
from enthought.chaco.api import ArrayPlotData, Plot

class Viewer(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.plotview = Plotter(self)
        self.setCentralWidget(self.plotview.widget)
        x = arange(10)
        y = sin(x)
        self.plotview.update_data(x, y)

class Plotter():
    def __init__(self, parent):
        self.plotdata = ArrayPlotData(x=array([]),  y=array([]))
        self.window = self.create_plot(parent)
        self.widget = self.window.control

    def update_data(self, x, y):
        self.plotdata.set_data("x", x)
        self.plotdata.set_data("y", y)

    def create_plot(self, parent):
        plot = Plot(self.plotdata, padding=50, border_visible=True)
        plot.plot(("x", "y"), name="data plot", color="green")
        return Window(parent, -1, component=plot)

if __name__ == "__main__":
    plot = Viewer()
    plot.resize(600, 400)
    plot.show()
    sys.exit(app.exec_())
