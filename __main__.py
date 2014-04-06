# Import required modules
import sys
from PySide import QtCore, QtGui

from GAApplication import GAApplication


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
