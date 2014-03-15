import numpy as np
from PySide import QtCore, QtGui

class GridVals:
    EMPTY = 0  # Nothing in this box
    FOOD  = 1  # There is food here
    START = 5  # The starting position of the ant.
    OPT   = 7  # The optimal route for the ant not containing food.
    END   = 8  # The optimal ending position for the ant.
    HIST  = 9  # The history of where the ant has been.

class Communicate(QtCore.QObject):
    
    msgToSB = QtCore.Signal(str)

class Trail(QtGui.QFrame):
    """ Our main window class
    """
    RECTANGLE_SIZE = 32
    SPEED          = 1000
    ROTATE_ANGLE   = 90
    ROTATE_MAX     = 360 - 1

    # Constructor function
    def __init__(self, parent):
        super(Trail, self).__init__()

        # Read in the data grid
        with open("trail7_6.dat", "r") as input_file:
            file_content = input_file.read().strip()
            file_content = file_content.replace('\r\n', ';')
            file_content = file_content.replace('\n', ';')
            file_content = file_content.replace('\r', ';')
        self.data_matrix = np.matrix(file_content)

        # Find and set the ant's present position.
        self.curY, self.curX = np.where(self.data_matrix == 5)
        self.curY = self.curY.item(0)
        self.curX = self.curX.item(0)

        # The ant's rotation.
        self.rot  = 0

        # Get the size of the data grid and decrement by 1 since board
        # grid starts at index 0.
        self.maxY, self.maxX = self.data_matrix.shape
        self.maxX = self.maxX - 1
        self.maxY = self.maxY - 1

        # Timer used for potential auto updating.
        self.timer     = QtCore.QBasicTimer()

        # Set this frame to have focus for keyboard.
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Variable to control if keyboard works for mvoement or not.
        self.keyboardMove = False

        # Used to update the status bar
        self.c = Communicate()

        # Holds a sequence of commands used to automatically move
        self.autoMoveStr = ""
        self.movePos     = 0

    def start(self):
        self.timer.start(Trail.SPEED, self)

    def queueAutoMove(self, strIn):
        self.autoMoveStr = strIn
        self.start()

    def moveForward(self):
        if self.rot == 0:
            self.moveUp()
        elif self.rot == 90:
            self.moveRight()
        elif self.rot == 180:
            self.moveDown()
        elif self.rot == 270:
            self.moveLeft()

    def leftRotate(self):
        self.rotateAnt(self.rot - self.ROTATE_ANGLE)

    def rightRotate(self):
        self.rotateAnt(self.rot + self.ROTATE_ANGLE)

    def moveUp(self):
        self.moveAnt(self.curX, self.curY - 1)

    def moveDown(self):
        self.moveAnt(self.curX, self.curY + 1)

    def moveRight(self):
        self.moveAnt(self.curX + 1, self.curY)

    def moveLeft(self):
        self.moveAnt(self.curX - 1, self.curY)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        # Paint the grid
        for x in range(self.data_matrix.shape[1]):
            for y in range(self.data_matrix.shape[0]):
                self.drawBox(painter, x, y, self.data_matrix.A[y][x])

        # Add the ant
        self.drawAnt(painter, self.curX, self.curY)

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.autoMoveStr[self.movePos] == "M":
                self.moveForward()
            elif self.autoMoveStr[self.movePos] == "L":
                self.leftRotate()
            elif self.autoMoveStr[self.movePos] == "R":
                self.rightRotate()

            self.movePos = self.movePos + 1

            if self.movePos >= len(self.autoMoveStr):
                self.c.msgToSB.emit("Routine Finished")
                self.timer.stop()

        else:
            QtGui.QFrame.timerEvent(self, event)

    def keyPressEvent(self, event):
        key = event.key()

        if not self.keyboardMove:
            self.c.msgToSB.emit("Keyboard movment is disabled!")
            QtGui.QWidget.keyPressEvent(self, event)
            return
        
        if key == QtCore.Qt.Key_Left or key == QtCore.Qt.Key_A:
            self.moveLeft()
        elif key == QtCore.Qt.Key_Right or key == QtCore.Qt.Key_D:
            self.moveRight()
        elif key == QtCore.Qt.Key_Down or key == QtCore.Qt.Key_S:
            self.moveDown()
        elif key == QtCore.Qt.Key_Up or key == QtCore.Qt.Key_W:
            self.moveUp()
        elif key == QtCore.Qt.Key_Q:
            self.leftRotate()
        elif key == QtCore.Qt.Key_E:
            self.rightRotate()
        else:
            QtGui.QWidget.keyPressEvent(self, event)

    def drawBox(self, painter, x, y, fill):
        colors = {}
        colors[GridVals.EMPTY] = QtGui.QColor(0,0,0,0)
        colors[GridVals.FOOD]  = QtGui.QColor(0,0,255,128)
        colors[GridVals.START] = QtGui.QColor(0,255,0,32)
        colors[GridVals.OPT]   = QtGui.QColor(0,0,255,64)
        colors[GridVals.END]   = QtGui.QColor(255,0,0,128)
        colors[GridVals.HIST]  = QtGui.QColor(255,153,204,128)

        brush = QtGui.QBrush(colors[fill])
        painter.setBrush(brush)

        painter.drawRect(x * self.RECTANGLE_SIZE, y * self.RECTANGLE_SIZE, 
            self.RECTANGLE_SIZE, self.RECTANGLE_SIZE)

        # If this box needs to contain food, draw it.
        if fill == GridVals.FOOD:
            self.drawFood(painter, x, y)

    def drawFood(self, painter, x, y):
        # Set up the brush and pen for circle and then draw it.
        brush = QtGui.QBrush(QtGui.QColor(255,255,0,255))
        pen   = QtGui.QPen(QtGui.QColor(0,0,0,255))
        painter.setBrush(brush)
        painter.setPen(pen)

        # Draw the circle centered in box with radius of 1/4 the circle
        center = QtCore.QPointF(self.RECTANGLE_SIZE * (x + 0.5),
            self.RECTANGLE_SIZE * (y + 0.5))
        radius = self.RECTANGLE_SIZE / 4
        painter.drawEllipse(center, radius, radius)

    def moveAnt(self, newX, newY):
        # Check if at the borders and then move ant.
        if newX > self.maxX:
            newX = newX - self.maxX - 1
        elif newX < 0:
            newX = self.maxX + newX + 1

        if newY > self.maxY:
            newY = newY - self.maxY - 1
        elif newY < 0:
            newY = self.maxY + newY + 1

        self.data_matrix[self.curY, self.curX] = GridVals.HIST

        self.curY = newY
        self.curX = newX

        # Check if the ant consumed food at new position.
        if self.data_matrix[self.curY, self.curX] > 0:
            self.data_matrix[self.curY, self.curX] = 0

        self.update()

    def rotateAnt(self, newRot):
        while newRot >= self.ROTATE_MAX:
            newRot = newRot - self.ROTATE_MAX

        while newRot < 0:
            newRot = newRot + self.ROTATE_MAX

        newRot = self.roundAngle(newRot)

        self.rot = newRot

        self.update()

    def drawAnt(self, painter, x, y):
        antpix = ()

        if(self.rot == 0):
            antpix = QtGui.QPixmap('images/ant_0.png')
        elif(self.rot == 90):
            antpix = QtGui.QPixmap('images/ant_90.png')
        elif(self.rot == 180):
            antpix = QtGui.QPixmap('images/ant_180.png')
        elif(self.rot == 270):
            antpix = QtGui.QPixmap('images/ant_270.png')



        painter.drawPixmap(x*self.RECTANGLE_SIZE, y*self.RECTANGLE_SIZE,
            antpix)


    def roundAngle(self, x, base=ROTATE_ANGLE):
        return int(base * round(float(x) / base))