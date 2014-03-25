import math
import numpy as np
from PySide import QtCore, QtGui
from AgentTrail import AgentTrail, GridVals

class Communicate(QtCore.QObject):
    msgToSB = QtCore.Signal(str)

class TrailUI(QtGui.QFrame):
    """ Trail class that is the central widget in the main window.
    """
    ROTATE_ANGLE   = 90
    ROTATE_MAX     = 360 - 1

    AGENT_DELTA_S  = "agent/move_delta"
    RECT_SIZE_S    = "trail/grid_size"

    DEFAULT_FILE   = "trails/john_muir_32.yaml"

    # Constructor function
    def __init__(self, parent):
        super(TrailUI, self).__init__()

        # Create an Agent Trail 
        self.agent_trail = AgentTrail()
        self.agent_trail.readTrail(self.DEFAULT_FILE)

        # Get the size of the data grid and decrement by 1 since board
        # grid starts at index 0.
        self.maxY, self.maxX = self.agent_trail.getTrailDim()
        self.maxX = self.maxX - 1
        self.maxY = self.maxY - 1

        # Timer used for potential auto updating.
        self.timer     = QtCore.QBasicTimer()

        # Set this frame to have focus for keyboard.
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Variable to control if keyboard works for mvoement or not.
        self.keyboardMove = True

        # Used to update the status bar
        self.c = Communicate()

        # Holds a sequence of commands used to automatically move
        self.autoMoveStr = ""
        self.movePos     = 0

        # Set the sizing policy and margins
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,
            QtGui.QSizePolicy.Minimum)

        # Used to get to settings
        self.settings = QtCore.QSettings()

        # Define some settings if they aren't defined
        if not self.settings.contains(self.RECT_SIZE_S):
            self.settings.setValue(self.RECT_SIZE_S, 16)

    @QtCore.Slot(str)
    def loadGrid(self, filename):
        self.pause()
        self.setUpdatesEnabled(False)

        self.agent_trail = AgentTrail()
        self.agent_trail.readTrail(filename)

        # Update the maximums
        self.maxY, self.maxX = self.agent_trail.getTrailDim()
        self.maxX = self.maxX - 1
        self.maxY = self.maxY - 1

        self.setUpdatesEnabled(True)

    @QtCore.Slot(int)
    def setAntSpeed(self, newSpeed):
        self.settings.setValue(self.AGENT_DELTA_S, newSpeed)
        self.timer.stop()
        self.timer.start(self.settings.value(self.AGENT_DELTA_S), self)

    def pause(self):
        self.timer.stop()

    def resume(self):
        self.timer.start(self.settings.value(self.AGENT_DELTA_S, 1000), self)

    def sizeHint(self):
        """Sets the size hint to preferrably two boxes larger than
        the minimum size of the maze.
        """
        return QtCore.QSize((self.maxX + 3) * 
            self.settings.value(self.RECT_SIZE_S),
            (self.maxY + 3) * self.settings.value(self.RECT_SIZE_S))

    def minimumSizeHint(self):
        """Sets the minimum size hint to the exact dimensions 
        of the maze.
        """
        return QtCore.QSize((self.maxX + 1) * 
            self.settings.value(self.RECT_SIZE_S),
            (self.maxY + 1) * self.settings.value(self.RECT_SIZE_S))
        
    def queueAutoMove(self, strIn):
        """Starts a series of autmoatic movments of ant passed a
        string with the motions to perform.

        Args:
        strIn (str): Motions for ant to perform. Valid options are
          * M - Move forward.
          * L - Rotate ant left 90 degrees.
          * R - Rotate ant right 90 degrees.
        """
        self.autoMoveStr = strIn
        self.timer.start(self.settings.value(self.AGENT_DELTA_S, 1000), self)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        # Get the grid from AgentTrail
        data_matrix = self.agent_trail.getMatrix()

        # Paint the grid
        for x in range(data_matrix.shape[1]):
            for y in range(data_matrix.shape[0]):
                self.__drawBox(painter, x, y, data_matrix.A[y][x])

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.autoMoveStr[self.movePos] == "M":
                self.agent_trail.moveForward()
            elif self.autoMoveStr[self.movePos] == "L":
                self.agent_trail.turnLeft()
            elif self.autoMoveStr[self.movePos] == "R":
                self.agent_trail.turnRight()

            self.movePos = self.movePos + 1

            if self.movePos >= len(self.autoMoveStr):
                self.c.msgToSB.emit("Routine Finished")
                self.timer.stop()

            self.update()

        else:
            QtGui.QFrame.timerEvent(self, event)

    def keyPressEvent(self, event):
        key = event.key()

        if not self.keyboardMove:
            self.c.msgToSB.emit("Keyboard movment is disabled!")
            QtGui.QWidget.keyPressEvent(self, event)
            return
        
        if key == QtCore.Qt.Key_Left or key == QtCore.Qt.Key_A:
            self.agent_trail.turnLeft()
        elif key == QtCore.Qt.Key_Right or key == QtCore.Qt.Key_D:
            self.agent_trail.turnRight()
        elif key == QtCore.Qt.Key_Up or key == QtCore.Qt.Key_W:
            self.agent_trail.moveForward()
        else:
            QtGui.QWidget.keyPressEvent(self, event)

        self.update()

    def __drawBox(self, painter, x, y, fill):
        colors = {}
        colors[GridVals.EMPTY]   = QtGui.QColor(0,0,0,0)
        colors[GridVals.FOOD]    = QtGui.QColor(0,0,255,128)
        colors[GridVals.ANT0]    = QtGui.QColor(0,255,0,255)
        colors[GridVals.ANT90]   = colors[GridVals.ANT0]
        colors[GridVals.ANT180]  = colors[GridVals.ANT0]
        colors[GridVals.ANT270]  = colors[GridVals.ANT0]
        colors[GridVals.OPT]     = QtGui.QColor(0,0,255,64)
        colors[GridVals.END]     = QtGui.QColor(255,0,0,128)
        colors[GridVals.HIST]    = QtGui.QColor(255,153,204,128)

        brush = QtGui.QBrush(colors[fill])
        painter.setBrush(brush)

        painter.drawRect(x * self.settings.value(self.RECT_SIZE_S), 
            y * self.settings.value(self.RECT_SIZE_S), 
            self.settings.value(self.RECT_SIZE_S),
            self.settings.value(self.RECT_SIZE_S))

        # If this box needs to contain food, draw it.
        if fill == GridVals.FOOD:
            self.__drawFood(painter, x, y)

        # If this box has the ant, draw it.
        if (fill == GridVals.ANT0 or
            fill == GridVals.ANT90 or
            fill == GridVals.ANT180 or
            fill == GridVals.ANT270):
            self.__drawAnt(painter, x, y, fill)

    def __drawFood(self, painter, x, y):
        painter.save()
        # Set up the brush and pen for circle and then draw it.
        brush = QtGui.QBrush(QtGui.QColor(255,255,0,255))
        pen   = QtGui.QPen(QtGui.QColor(0,0,0,255))
        painter.setBrush(brush)
        painter.setPen(pen)

        # Draw the circle centered in box with radius of 1/4 the circle
        center = QtCore.QPointF(
            self.settings.value(self.RECT_SIZE_S) * (x + 0.5),
            self.settings.value(self.RECT_SIZE_S) * (y + 0.5))
        radius = self.settings.value(self.RECT_SIZE_S) / 4
        painter.drawEllipse(center, radius, radius)
        painter.restore()

    def __drawAnt(self, painter, x, y, fill):
        # Save the current state of the painter
        painter.save()

        triPath = QtGui.QPainterPath()

        sqSize = self.settings.value(self.RECT_SIZE_S)

        left = QtCore.QPointF(0, sqSize)
        top = QtCore.QPointF(sqSize / 2, 0)
        right = QtCore.QPointF(sqSize, sqSize)

        # Start in bottom left, move to top middle, bottom right, back to bottom left.
        triPath.moveTo(left)
        triPath.lineTo(top)
        triPath.lineTo(right)
        triPath.lineTo(left)

        # Translate the coordinates of this point to the appropriate place on the grid.
        painter.translate(x * sqSize, y * sqSize)

        # If necessary, rotate and then translate appropriately.
        if(fill == GridVals.ANT90):
            painter.rotate(90)
            painter.translate(0, -sqSize)
        elif(fill == GridVals.ANT180):
            painter.rotate(180)
            painter.translate(-sqSize, -sqSize)
        elif(fill == GridVals.ANT270):
            painter.rotate(270)
            painter.translate(-sqSize, 0)

        # Actually paint the shape now.
        painter.setPen(QtGui.QPen(QtGui.QColor(0,0,0,255)))
        painter.fillPath(triPath, QtGui.QBrush(QtGui.QColor("black")))
        
        painter.restore()



