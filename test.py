# Import required modules
import sys
import time
from numpy import matrix
from PySide import QtCore, QtGui

from Trail import Trail
from Pixmap import Pixmap
from TrailConf import TrailConf

class GAApplication(QtGui.QMainWindow):

    def __init__(self):
        super(GAApplication, self).__init__()

        self.setGeometry(300, 300, 100, 100)
        self.setWindowTitle('Genetic Algorithm Tools')

        self.antTrailConf = TrailConf(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.antTrailConf)

        self.antTrail = Trail(self, self.antTrailConf)
        self.antTrail.setContentsMargins(0,0,0,0)
        self.setCentralWidget(self.antTrail)

        # Connect the signal/slot for the status bar.
        self.statusbar = self.statusBar()
        self.antTrail.c.msgToSB[str].connect(self.statusbar.showMessage)

        # Connect the signal/slot for the configuration
        self.antTrailConf.c.newFile[str].connect(self.antTrail.loadGrid)
        self.antTrailConf.c.newSpeed[int].connect(self.antTrail.setAntSpeed)
        
        self.antTrail.queueAutoMove("MMMMLRLMMMMMLMMM")


def main():
    # Exception Handling
    try:
        myApp = QtGui.QApplication(sys.argv)
        gaa   = GAApplication()
        gaa.show()
        sys.exit(myApp.exec_())
    except NameError:
        print("Name Error:", sys.exc_info()[1])
    except SystemExit:
        print("Closing Window...")
    except Exception:
        print (sys.exc_info()[1])


if __name__ == '__main__':
    main()