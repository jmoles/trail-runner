# Import required modules
import sys
import time
from numpy import matrix
from PySide import QtCore, QtGui

# PyQt doesn't support deriving from more than one wrapped class so we use
# composition and delegate the property.
class Pixmap(QtCore.QObject):
    def __init__(self, pix):
        super(Pixmap, self).__init__()

        self.pixmap_item = QtGui.QGraphicsPixmapItem(pix)
        self.pixmap_item.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)

    def set_pos(self, pos):
        self.pixmap_item.setPos(pos)

    def get_pos(self):
        return self.pixmap_item.pos()

    def set_rotate(self, rotate):
        self.pixmap_item.prepareGeometryChange()
        self.pixmap_item.rotate(rotate)

    def get_rotate(self):
        return self.pixmap_item.rotation()

    pos = QtCore.Property(QtCore.QPointF, get_pos, set_pos)
    rotate = QtCore.Property(float, get_rotate, set_rotate)

class MainWindow(QtGui.QMainWindow):
    """ Our main window class
    """
    RECTANGLE_SIZE = 32
    scene = []

    # Constructor function
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Sample Window")
        self.setGeometry(100, 100, 640, 640)
        self.setMinimumHeight(500)
        self.setMinimumWidth(400)


    def CreateStatusBar(self):
        self.myStatusBar = QtGui.QStatusBar()
        self.myStatusBar.showMessage('Ready')
        self.setStatusBar(self.myStatusBar)

    def SetupComponents(self):
        view = QtGui.QGraphicsView()
        view.setWindowTitle("Ants")
        view.setViewportUpdateMode(QtGui.QGraphicsView.BoundingRectViewportUpdate)
        view.setBackgroundBrush(QtGui.QPixmap("kitten.jpg"))
        view.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        view.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.setCentralWidget(view)

        self.scene = QtGui.QGraphicsScene()

        self.buildGrid()
        view.setScene(self.scene)
        view.show()

    def AddItem(self, item):
        self.scene.addItem(ant.pixmap_item)

    def buildGrid(self):
        # From http://www.topbug.net/blog/2013/01/10/load-a-matrix-from-an-ascii-format-file/
        with open("trail5.dat", "r") as input_file:
            file_content = input_file.read().strip()
            file_content = file_content.replace('\r\n', ';')
            file_content = file_content.replace('\n', ';')
            file_content = file_content.replace('\r', ';')

            data_matrix = matrix(file_content)

        num_x = data_matrix.shape[1]
        num_y = data_matrix.shape[0]

        # Go through each cell and paint the colors
        # 0 indicates an empty cell
        # 1 is a food location
        # 5 is the starting location
        # 8 is the last food location
        for x in range(num_x):
            for y in range(num_y):
                if(data_matrix.A[y][x] == 0):
                    brush = QtGui.QBrush(QtGui.QColor(0,0,0,0))
                elif(data_matrix.A[y][x] == 1):
                    brush = QtGui.QBrush(QtGui.QColor(0,0,255,128))
                elif(data_matrix.A[y][x] == 5):
                    brush = QtGui.QBrush(QtGui.QColor(0,255,0,32))
                elif(data_matrix.A[y][x] == 8):
                    brush = QtGui.QBrush(QtGui.QColor(255,0,0,128))
                self.scene.addRect(x*self.RECTANGLE_SIZE, y*self.RECTANGLE_SIZE, 
                    self.RECTANGLE_SIZE, self.RECTANGLE_SIZE, QtGui.QPen(), brush)

if __name__ == '__main__':
    # Exception Handling
    try:
        myApp = QtGui.QApplication(sys.argv)
        myWindow = MainWindow()
        myWindow.CreateStatusBar()
        myWindow.SetupComponents()
        myWindow.show()

        ant = Pixmap(QtGui.QPixmap("images/ant_0.png"))
        myWindow.AddItem(ant)
        rootState = QtCore.QState()
        state1 = QtCore.QState(rootState)
        state2 = QtCore.QState(rootState)
        state3 = QtCore.QState(rootState)
        state4 = QtCore.QState(rootState)
        state5 = QtCore.QState(rootState)
        state6 = QtCore.QState(rootState)
        state7 = QtCore.QState(rootState)
        state8 = QtCore.QState(rootState)

        state1.assignProperty(ant, 'pos',
            QtCore.QPointF(3*32, 4*32))

        state2.assignProperty(ant, 'pos',
            QtCore.QPointF(3*32, 3*32))

        state3.assignProperty(ant, 'pos',
            QtCore.QPointF(3*32, 2*32))

        state4.assignProperty(ant, 'pos',
            QtCore.QPointF(3*32, 1*32))

        state5.assignProperty(ant, 'rotate',
            270)

        # Had to move down a row because of rotation above messes up position.
        state5.assignProperty(ant, 'pos',
            QtCore.QPointF(3*32, 2*32))

        state6.assignProperty(ant, 'pos',
            QtCore.QPointF(2*32, 2*32))

        state7.assignProperty(ant, 'pos',
            QtCore.QPointF(1*32, 2*32))

        state8.assignProperty(ant, 'pos',
            QtCore.QPointF(0*32, 2*32))

        states = QtCore.QStateMachine()
        states.addState(rootState)
        states.setInitialState(rootState)
        rootState.setInitialState(state1)

        anim = QtCore.QPropertyAnimation(ant, "pos")
        anim.setDuration(200)

        states.addDefaultAnimation(anim)

        timer1 = QtCore.QTimer()
        timer1.setSingleShot(True)

        timer2 = QtCore.QTimer()
        timer2.setSingleShot(True)

        timer3 = QtCore.QTimer()
        timer3.setSingleShot(True)

        timer4 = QtCore.QTimer()
        timer4.setSingleShot(True)

        timer5 = QtCore.QTimer()
        timer5.setSingleShot(True)

        timer6 = QtCore.QTimer()
        timer6.setSingleShot(True)

        timer7 = QtCore.QTimer()
        timer7.setSingleShot(True)

        timer8 = QtCore.QTimer()
        timer8.setSingleShot(True)
        
        rootState.addTransition(timer1.timeout, state1) 
        rootState.addTransition(timer2.timeout, state2)
        rootState.addTransition(timer3.timeout, state3)
        rootState.addTransition(timer4.timeout, state4)
        rootState.addTransition(timer5.timeout, state5)
        rootState.addTransition(timer6.timeout, state6)
        rootState.addTransition(timer7.timeout, state7)
        rootState.addTransition(timer8.timeout, state8)

        timer1.start(1000)
        timer2.start(2000)
        timer3.start(3000)
        timer4.start(4000)
        timer5.start(5000)
        timer6.start(6000)
        timer7.start(7000)
        timer8.start(8000)

        states.start()      

        sys.exit(myApp.exec_())
    except NameError:
        print("Name Error:", sys.exc_info()[1])
    except SystemExit:
        print("Closing Window...")
    except Exception:
        print (sys.exc_info()[1])