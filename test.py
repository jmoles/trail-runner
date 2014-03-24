# Import required modules
import sys
import time
from numpy import matrix
from PySide import QtCore, QtGui

from Trail import Trail
from TrailConf import TrailConf

class Communicate(QtCore.QObject):
    newFile  = QtCore.Signal(str)
    newSpeed = QtCore.Signal(int)

class GAApplication(QtGui.QMainWindow):

    def __init__(self):
        super(GAApplication, self).__init__()

        # Configure and open settings
        QtCore.QCoreApplication.setOrganizationName("Josh Moles")
        QtCore.QCoreApplication.setOrganizationDomain("joshmoles.com")
        QtCore.QCoreApplication.setApplicationName("Ant Trail")
        self.settings = QtCore.QSettings()

        self.setWindowTitle('Genetic Algorithm Tools')
        self.c = Communicate()

        self.readSettings()

        self.antTrail = Trail(self)
        self.antTrail.setContentsMargins(0,0,0,0)
        self.setCentralWidget(self.antTrail)

        # Get the handle to the statusbar.
        self.statusbar = self.statusBar()

        # Create actions
        self.createActions()

        # Create the menu bar
        self.createMenus()

        # Connect the signals and slots
        self.connectSigSlot()

        self.antTrail.queueAutoMove("R")


    def writeSettings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.endGroup()

    def readSettings(self):
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size", QtCore.QSize(300, 300)))
        self.move(self.settings.value("pos", QtCore.QPoint(200, 200)))
        self.settings.endGroup()

    def closeEvent(self, event):
        self.writeSettings()
        self.settings.sync()
        QtGui.QMainWindow.closeEvent(self, event)

    def createActions(self):
        self.openTrailAct = QtGui.QAction("&Open Trail...", self, shortcut="Ctrl+O",
            triggered = self.openFile)
        self.exitAct = QtGui.QAction("E&xit", self, triggered=self.close)       
        
    def createMenus(self): 
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openTrailAct)
        self.fileMenu.addAction(self.exitAct)

    def connectSigSlot(self):
        # Connect the signal/slot for the status bar.
        self.antTrail.c.msgToSB[str].connect(self.statusbar.showMessage)

        # Connect the signal/slot for the configuration
        self.c.newFile[str].connect(self.antTrail.loadGrid)

    def openFile(self):
        filename, _ = QtGui.QFileDialog.getOpenFileName(self,
            str("Open Trail File"), ".", str("Trail Files (*.txt *.dat)"))

        if filename != "":
            self.c.newFile.emit(filename)


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