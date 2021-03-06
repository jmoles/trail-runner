import logging
import numpy as np
import sys

from ..DBUtils import DBUtils

class GridVals:
    EMPTY  = 0 # Nothing in this square
    FOOD   = 1 # There is food/trail here.
    ANT0   = 2 # Agent's position facing top.
    ANT90  = 3 # Agent's position facing left.
    ANT180 = 4 # Agent's position facing down.
    ANT270 = 5 # Agent's position facing right.
    OPT    = 7 # Optimal route for the agent.
    END    = 8 # Optimal ending point for the agent.
    HIST   = 9 # History of the agent.

    # List here for testing scripts.
    FULL_LIST = [EMPTY, FOOD, ANT0, ANT90, ANT180, ANT270, OPT, END, HIST]


class trail:
    """ Class to handle the trail for the agent to move through.
    """
    # Constants
    ROTATE_ANGLE = 90
    ROTATE_MAX   = 360 - 1

    def __init__(self):
        # Properties of the trail
        self.__data_matrix   = ()
        self.__rotation      = 0
        self.__trail_name    = ""
        self.__maxX          = 0
        self.__maxY          = 0
        self.__food_total    = 0

        # Properties of the agent
        self.__curr_agent    = GridVals.ANT0
        self.__currX         = 0
        self.__currY         = 0
        self.__food_consumed = 0

        self.__moves            = {}
        self.__moves["left"]    = 0
        self.__moves["right"]   = 0
        self.__moves["forward"] = 0
        self.__moves["none"]    = 0


    def readTrail(self, trail_num, db_config_file):
        pgdb = DBUtils(config_file=db_config_file)

        (self.__data_matrix,
        self.__trail_name,
        self.__rotation) = pgdb.getTrailData(trail_num)

        # Get the count of types of things in the maze.
        elem_count = np.bincount(np.ravel(self.__data_matrix))
        self.__food_total  = elem_count[GridVals.FOOD]

        if self.__food_total < 1:
            print "WARNING: This trail has no food in it!"

        self.__maxY, self.__maxX = self.__data_matrix.shape
        self.__maxX            = self.__maxX - 1
        self.__maxY            = self.__maxY - 1

        self.__updateAgentPos()

        # Determine the ant's current type and position
        self.__updateAgentRotType()


    def readTrailInstant(self, trail_m, trail_s, rot_i):
        self.__data_matrix = np.matrix(trail_m)
        self.__trail_name  = trail_s
        self.__rotation    = rot_i

        # Get the count of types of things in the maze.
        elem_count = np.bincount(np.ravel(self.__data_matrix))
        self.__food_total  = elem_count[GridVals.FOOD]

        if self.__food_total < 1:
            print "WARNING: This trail has no food in it!"

        self.__maxY, self.__maxX = self.__data_matrix.shape
        self.__maxX            = self.__maxX - 1
        self.__maxY            = self.__maxY - 1

        self.__updateAgentPos()

        # Determine the ant's current type and position
        self.__updateAgentRotType()


    def moveForward(self):
        """ Moves the agent forward a square relative to its current position.
        """
        if self.__rotation == 0:
            self.__moveUp()
        elif self.__rotation == 90:
            self.__moveRight()
        elif self.__rotation == 180:
            self.__moveDown()
        elif self.__rotation == 270:
            self.__moveLeft()

        self.__moves["forward"] += 1

    def turnLeft(self):
        """ Rotates the agent 90 degrees left.
        """
        self.__rotateAgent(self.__rotation - self.ROTATE_ANGLE)

        self.__moves["left"] += 1


    def turnRight(self):
        """ Rotates the agent 90 degrees right.
        """
        self.__rotateAgent(self.__rotation + self.ROTATE_ANGLE)

        self.__moves["right"] += 1

    def noMove(self):
        """ Does not move the agent. Just increments the number of moves taken.
        """
        self.__moves["none"] += 1

    def getFoodConsumed(self):
        """ Returns the amount of food consumed.

        Returns:
            int. Amount of food consumed.
        """
        return self.__food_consumed

    def isFoodAhead(self):
        """ Determines if there is food in front of the agent.

        Returns:
            list. X, Y coordinates of the spot in front of the agent.
        """
        (xAhead, yAhead) = self.__squareAhead()

        if(self.__data_matrix[yAhead, xAhead] == GridVals.FOOD or
            self.__data_matrix[yAhead, xAhead] == GridVals.END):
            return True
        else:
            return False

    def getNumMoves(self):
        """ Returns the number of moves the agent has made.

        Returns:
            int. Number of moves that agent has made.
        """
        return sum(self.__moves.values())

    def getMovesStats(self):
        """ Returns a dictionary with a count of types of moves made.

        Returns:
            dict. With keys "left", "right", "forward", "none" with move count.
        """

        return self.__moves

    def getFoodStats(self):
        """ Returns the current statistics on the agent's food.

        Returns:
            list. Food consumed (int), food remaining (int)
        """
        return (self.__food_consumed, self.__food_total - self.__food_consumed)

    def getName(self):
        """ Returns the friendly name of this trail.

        Returns:
            str. Friendly name of the trail.
        """
        return self.__trail_name

    def getTrailDim(self):
        """ Get the dimenions of the current trail.

        Returns:
            list. X, Y size of the current trail.
        """
        maxY, maxX = self.__data_matrix.shape

        return (maxX, maxY)

    def getMatrix(self):
        """ Returns the data matrix.
        """
        return self.__data_matrix

    def __squareAhead(self):
        """ Determines the square in front of the agent based off present position.

        Returns:
            list. X, Y coordinates of the square in front of the ant.
        """
        newX = self.__currX
        newY = self.__currY

        # Find the point where the agent would ideally move to.
        if self.__rotation == 0:
            newY = newY - 1
        elif self.__rotation == 90:
            newX = newX + 1
        elif self.__rotation == 180:
            newY = newY + 1
        elif self.__rotation == 270:
            newX = newX - 1

        # Check if the agent exceeds the minimums and maximums.
        if newX > self.__maxX:
            newX = newX - self.__maxX - 1
        elif newX < 0:
            newX = self.__maxX + newX + 1
        if newY > self.__maxY:
            newY = newY - self.__maxY - 1
        elif newY < 0:
            newY = self.__maxY + newY + 1

        return (newX, newY)


    def __moveUp(self):
        """ Moves the agent up a square.
        """
        self.__moveAgent(self.__currX, self.__currY - 1)

    def __moveDown(self):
        """ Moves the agent down a square.
        """
        self.__moveAgent(self.__currX, self.__currY + 1)

    def __moveRight(self):
        """ Moves the agent right a square.
        """
        self.__moveAgent(self.__currX + 1, self.__currY)

    def __moveLeft(self):
        """ Moves the agent left a square.
        """
        self.__moveAgent(self.__currX - 1, self.__currY)


    def __moveAgent(self, newX, newY):
        # Check if at the borders and then move ant.
        if newX > self.__maxX:
            newX = newX - self.__maxX - 1
        elif newX < 0:
            newX = self.__maxX + newX + 1
        if newY > self.__maxY:
            newY = newY - self.__maxY - 1
        elif newY < 0:
            newY = self.__maxY + newY + 1

        self.__data_matrix[self.__currY, self.__currX] = GridVals.HIST

        self.__currY = newY
        self.__currX = newX

        # Move has occurred. Now, do steps at new spot.

        # Check if the ant consumed food at the new spot
        if (self.__data_matrix[self.__currY, self.__currX] == GridVals.FOOD or
            self.__data_matrix[self.__currY, self.__currX] == GridVals.END):
            self.__food_consumed = self.__food_consumed + 1
            self.__data_matrix[self.__currY, self.__currX] = GridVals.EMPTY
        else:
            self.__data_matrix[self.__currY, self.__currX] = (
                self.__data_matrix[self.__currY, self.__currX])

        # Set agent to this position.
        self.__data_matrix[self.__currY, self.__currX] = self.__curr_agent



    def __rotateAgent(self, newRot):
        while newRot >= self.ROTATE_MAX:
            newRot = newRot - self.ROTATE_MAX

        while newRot < 0:
            newRot = newRot + self.ROTATE_MAX

        newRot = self.__roundAngle(newRot)

        self.__rotation = newRot
        self.__updateAgentRotType()


    def __updateAgentPos(self):

        # Get the count of types of things in the maze.
        elem_count = np.bincount(np.ravel(self.__data_matrix))

        if np.sum(elem_count[2:6] > 1):
            # Big error. We have two agents in maze.
            logging.error("There are two agents in the maze!")
            sys.exit(1)

        if (elem_count[GridVals.ANT0] == 1):
            currPos = np.where(self.__data_matrix == GridVals.ANT0)
        elif(elem_count[GridVals.ANT90] == 1):
            currPos = np.where(self.__data_matrix == GridVals.ANT90)
        elif(elem_count[GridVals.ANT180] == 1):
            currPos = np.where(self.__data_matrix == GridVals.ANT180)
        elif(elem_count[GridVals.ANT270] == 1):
            currPos = np.where(self.__data_matrix == GridVals.ANT270)

        self.__currY = currPos[0].item(0)
        self.__currX = currPos[1].item(0)


    def __updateAgentRotType(self):
        if (self.__rotation == 0):
            self.__curr_agent = GridVals.ANT0
        elif(self.__rotation == 90):
            self.__curr_agent = GridVals.ANT90
        elif(self.__rotation == 180):
            self.__curr_agent = GridVals.ANT180
        elif(self.__rotation == 270):
            self.__curr_agent = GridVals.ANT270

        self.__data_matrix[self.__currY, self.__currX] = self.__curr_agent

    def __roundAngle(self, x, base=ROTATE_ANGLE):
        return int(base * round(float(x) / base))
