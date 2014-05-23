import math
import numpy as np
from PySide import QtCore, QtGui
from ..trail.trail import trail as AgentTrail
from ..trail.trail import GridVals

from .settings import settings as GASettings

class Solarized():
    BASE03  = QtGui.QColor("#002b36")
    BASE02  = QtGui.QColor("#073642")
    BASE01  = QtGui.QColor("#586e75")
    BASE00  = QtGui.QColor("#657b83")
    BASE0   = QtGui.QColor("#839496")
    BASE1   = QtGui.QColor("#93a1a1")
    BASE2   = QtGui.QColor("#eee8d5")
    BASE3   = QtGui.QColor("#fdf6e3")
    YELLOW  = QtGui.QColor("#b58900")
    ORANGE  = QtGui.QColor("#cb4b16")
    RED     = QtGui.QColor("#dc322f")
    MAGENTA = QtGui.QColor("#d33682")
    VIOLET  = QtGui.QColor("#6c71c4")
    BLUE    = QtGui.QColor("#268bd2")
    CYAN    = QtGui.QColor("#2aa198")
    GREEN   = QtGui.QColor("#859900")

class Communicate(QtCore.QObject):
    msgToSB = QtCore.Signal(str)

class trail(QtGui.QFrame):
    """ Trail class that is the central widget in the main window.
    """
    ROTATE_ANGLE   = 90
    ROTATE_MAX     = 360 - 1

    AGENT_DELTA_S  = "trailUI/agent_delta"
    RECT_SIZE_S    = "trailUI/rect_size"

    # Constructor function
    def __init__(self, parent, trail_num):
        super(trail, self).__init__()

        # Used to get to settings
        self.settings = GASettings()

        # Create an Agent Trail
        self.agent_trail = AgentTrail()
        self.agent_trail.readTrail(trail_num)

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

        self.__agent_delta = int(self.settings.value(trail.AGENT_DELTA_S))
        self.__grid_size   = int(self.settings.value(trail.RECT_SIZE_S))

        self.__last_number = ""

    @QtCore.Slot(str)
    def loadGrid(self, trail_num):
        self.pause()
        self.setUpdatesEnabled(False)

        self.agent_trail = AgentTrail()
        self.agent_trail.readTrail(trail_num)
        self.__last_number = trail_num

        # Update the maximums
        self.maxY, self.maxX = self.agent_trail.getTrailDim()
        self.maxX = self.maxX - 1
        self.maxY = self.maxY - 1

        self.setUpdatesEnabled(True)

    @QtCore.Slot(bool)
    def settingsUpdated(self):
        self.__agent_delta = int(self.settings.value(trail.AGENT_DELTA_S))
        self.__grid_size   = int(self.settings.value(trail.RECT_SIZE_S))

        if self.timer.isActive():
            self.timer.stop()
            self.timer.start(self.__agent_delta, self)

    def pause(self):
        self.timer.stop()

    def resume(self):
        self.timer.start(self.__agent_delta, self)

    def sizeHint(self):
        """Sets the size hint to preferrably two boxes larger than
        the minimum size of the maze.
        """
        return QtCore.QSize((self.maxX + 3) *
            self.__grid_size,
            (self.maxY + 4) * self.__grid_size)

    def minimumSizeHint(self):
        """Sets the minimum size hint to the exact dimensions
        of the maze.
        """
        return QtCore.QSize((self.maxX + 1) *
            self.__grid_size,
            (self.maxY + 2) * self.__grid_size)

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
        self.movePos     = 0
        self.timer.start(self.__agent_delta, self)

    def paintEvent(self, event):
        # Get the grid from AgentTrail
        data_matrix = self.agent_trail.getMatrix()

        # Determine the extents and add a padding square
        self.maxY, self.maxX = self.agent_trail.getTrailDim()

        painter = QtGui.QPainter(self)
        painter.translate(2 * self.__grid_size,
            2 * self.__grid_size)
        painter.fillRect(0, 0,
            (self.maxX) * self.__grid_size,
            (self.maxY) * self.__grid_size,
            QtGui.QBrush(Solarized.BASE3))

        # Paint the grid
        for x in range(data_matrix.shape[1]):
            for y in range(data_matrix.shape[0]):
                self.__drawBox(painter, x, y, data_matrix.A[y][x])

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.autoMoveStr[self.movePos] == "N":
                self.agent_trail.noMove()
            elif self.autoMoveStr[self.movePos] == "M":
                self.agent_trail.moveForward()
            elif self.autoMoveStr[self.movePos] == "L":
                self.agent_trail.turnLeft()
            elif self.autoMoveStr[self.movePos] == "R":
                self.agent_trail.turnRight()

            self.movePos = self.movePos + 1

            if self.movePos >= len(self.autoMoveStr):
                self.c.msgToSB.emit("Routine Finished")
                self.timer.stop()

            self.__updateStatusBar()

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

        self.__updateStatusBar()

        self.update()

    def __updateStatusBar(self):
        # Gather information
        moves = self.agent_trail.getNumMoves()
        foodl = self.agent_trail.getFoodStats()

        sbSendMessage = ("Moves: " + str(moves) +
            " Food Consumed / Remaining / Total: " +
            str(foodl[0]) + " / " + str(foodl[1]) + " / " +
            str(foodl[0] + foodl[1]))

        # Display information
        self.c.msgToSB.emit(sbSendMessage)

    def __drawBox(self, painter, x, y, fill):
        painter.save()
        colors = {}
        colors[GridVals.EMPTY]   = Solarized.BASE3
        colors[GridVals.FOOD]    = Solarized.BLUE
        colors[GridVals.ANT0]    = Solarized.BASE1
        colors[GridVals.ANT90]   = colors[GridVals.ANT0]
        colors[GridVals.ANT180]  = colors[GridVals.ANT0]
        colors[GridVals.ANT270]  = colors[GridVals.ANT0]
        colors[GridVals.OPT]     = Solarized.CYAN
        colors[GridVals.END]     = QtGui.QColor(255,0,0,128)
        colors[GridVals.HIST]    = Solarized.BASE0

        painter.setPen(QtGui.QPen(Solarized.BASE03))
        painter.setBrush(QtGui.QBrush(colors[fill]))

        painter.drawRect(x * self.__grid_size,
            y * self.__grid_size,
            self.__grid_size,
            self.__grid_size)

        # If this box needs to contain food,soa draw it.
        if fill == GridVals.FOOD:
            self.__drawFood(painter, x, y)

        # If this box has the ant, draw it.
        if (fill == GridVals.ANT0 or
            fill == GridVals.ANT90 or
            fill == GridVals.ANT180 or
            fill == GridVals.ANT270):
            self.__drawAgent(painter, x, y, fill)

        painter.restore()

    def __drawFood(self, painter, x, y):
        painter.save()
        # Set up the brush and pen for circle and then draw it.
        brush = QtGui.QBrush(Solarized.YELLOW)
        pen   = QtGui.QPen(QtGui.QColor(0,0,0,255))
        painter.setBrush(brush)
        painter.setPen(pen)

        # Draw the circle centered in box with radius of 1/4 the circle
        center = QtCore.QPointF(
            self.__grid_size * (x + 0.5),
            self.__grid_size * (y + 0.5))
        radius = self.__grid_size / 4
        painter.drawEllipse(center, radius, radius)
        painter.restore()

    def __drawAgent(self, painter, x, y, fill):
        # Save the current state of the painter
        painter.save()

        triPath = QtGui.QPainterPath()

        sqSize = self.__grid_size

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
        painter.setPen(QtGui.QPen(Solarized.ORANGE))
        painter.fillPath(triPath, QtGui.QBrush(Solarized.ORANGE))

        painter.restore()



