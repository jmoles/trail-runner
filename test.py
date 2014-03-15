# Import required modules
import sys
import time
from numpy import matrix
from PySide import QtCore, QtGui

from Trail import Trail
from Pixmap import Pixmap

class GAApplication(QtGui.QMainWindow):

    def __init__(self):
        super(GAApplication, self).__init__()

        self.setGeometry(300, 300, 640, 640)
        self.setWindowTitle('Genetic Algorithm Tools')
        self.AntTrail = Trail(self)

        self.setCentralWidget(self.AntTrail)

        self.statusbar = self.statusBar()
        self.AntTrail.c.msgToSB[str].connect(self.statusbar.showMessage)
        
        self.AntTrail.queueAutoMove("MMMMLRLMMMMMLMMM")

        self.center()
        
    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size =  self.geometry()
        self.move((screen.width()-size.width())/2, 
            (screen.height()-size.height())/2)

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