# Import required modules
import sys
import time
from numpy import matrix
from PySide.QtGui import (QApplication, QStatusBar, QMainWindow, QGraphicsView,
	QGraphicsScene, QGraphicsPixmapItem, QPixmap, QPen, QBrush, QColor,
	QGraphicsItemAnimation)
from PySide.QtCore import QTimeLine, QPointF

class MainWindow(QMainWindow):
    """ Our main window class
    """

    # Constructor function
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("Sample Window")
        self.setGeometry(100, 100, 640, 640)
        self.setMinimumHeight(500)
        self.setMinimumWidth(400)


    def CreateStatusBar(self):
        self.myStatusBar = QStatusBar()
        self.myStatusBar.showMessage('Ready')
        self.setStatusBar(self.myStatusBar)

    def SetupComponents(self):
        view = QGraphicsView()
        self.setCentralWidget(view)

        scene = QGraphicsScene()
        # kitten = QGraphicsPixmapItem(QPixmap("kitten.jpg"))
        # scene.addItem(kitten)
        self.buildGrid(scene)
        view.setScene(scene)
        view.show()


    def buildGrid(self, scene):
        rectangle_size = 32

        # From http://www.topbug.net/blog/2013/01/10/load-a-matrix-from-an-ascii-format-file/
        with open("trail5.dat", "r") as input_file:
            file_content = input_file.read().strip()
            file_content = file_content.replace('\r\n', ';')
            file_content = file_content.replace('\n', ';')
            file_content = file_content.replace('\r', ';')

            data_matrix = matrix(file_content)

        num_x = data_matrix.shape[1]
        num_y = data_matrix.shape[0]

        ant = QGraphicsPixmapItem(QPixmap("ant.png"))
        # Go through each cell and paint the colors
        # 0 indicates an empty cell
        # 1 is a food location
        # 5 is the starting location
        # 8 is the last food location
        for x in range(num_x):
            for y in range(num_y):
                if(data_matrix.A[y][x] == 0):
                    brush = QBrush(QColor(0,0,0,0))
                elif(data_matrix.A[y][x] == 1):
                    brush = QBrush(QColor(0,0,255,128))
                elif(data_matrix.A[y][x] == 5):
                    brush = QBrush(QColor(0,255,0,32))
                    ant.setOffset(x*rectangle_size, y*rectangle_size)
                    scene.addItem(ant)
                elif(data_matrix.A[y][x] == 8):
                    brush = QBrush(QColor(255,0,0,128))

                scene.addRect(x*rectangle_size, y*rectangle_size, 
                    rectangle_size, rectangle_size, QPen(), brush)
        

if __name__ == '__main__':
    # Exception Handling
    try:
        myApp = QApplication(sys.argv)
        myWindow = MainWindow()
        myWindow.CreateStatusBar()
        myWindow.setWindowTitle("Ant Trail")
        myWindow.SetupComponents()
        myWindow.show()
        myApp.exec_()
        sys.exit(0)
    except NameError:
        print("Name Error:", sys.exc_info()[1])
    except SystemExit:
        print("Closing Window...")
    except Exception:
        print (sys.exc_info()[1])