import numpy as np
import yaml

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

class AgentTrail:
    """ Class to handle the trail for the agent to move through.
    """
    # Constants
    ROTATE_ANGLE = 90
    ROTATE_MAX   = 360

    def __init__(self):
        # Properties of the trail
        self.__data_matrix  = ()
        self.__rotation     = 0
        self.__trail_name   = ""
        self.__maxX         = 0
        self.__maxY         = 0

        # Properties of the agent
        self.__currAgent    = GridVals.ANT0
        self.__currX        = 0
        self.__currY        = 0
        self.__foodConsumed = 0


    def readTrail(self, filename):
        with open(filename, "r") as input_file:
            file_content = input_file.read()

        yaml_in = yaml.load(file_content)

        trail = yaml_in["trail"]

        trail = trail.replace('\r\n', ';')
        trail = trail.replace('\n', ';')
        trail = trail.replace('\r', ';')

        self.__data_matrix = np.matrix(trail)
        self.__rotation    = yaml_in["init_rot"]
        self.__trail_name  = yaml_in["name"]

        self.__maxY, self.__maxX = self.__data_matrix.shape
        self.__maxX            = self.__maxX - 1
        self.__maxY            = self.__maxY - 1

        # Determine the ant's current type and position
        self.__updateAgentRotType()

        self.__currY, self.__currX = np.where(self.__data_matrix == self.__currAgent)
        self.__currY = self.__currY.item(0)
        self.__currX = self.__currX.item(0)

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

    def turnLeft(self):
        """ Rotates the agent 90 degrees left.
        """
        self.__rotateAgent(self.__rotation - self.ROTATE_ANGLE)


    def turnRight(self):
        """ Rotates the agent 90 degrees right.
        """
        self.__rotateAgent(self.__rotation + self.ROTATE_ANGLE)

    def getFoodConsumed(self):
        """ Returns the amount of food consumed.

        Returns:
            int. Amount of food consumed.
        """
        return self.__foodConsumed

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

    def printDataMatrix(self):
        np.set_printoptions(threshold='nan')
        print self.__data_matrix


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
            self.__foodConsumed = self.__foodConsumed + 1
            self.__data_matrix[self.__currY, self.__currX] = GridVals.EMPTY
        else:
            self.__data_matrix[self.__currY, self.__currX] = (
                self.__data_matrix[self.__currY, self.__currX])
        
        # Set agent to this position.
        self.__data_matrix[self.__currY, self.__currX] = self.__currAgent



    def __rotateAgent(self, newRot):
        while newRot >= self.ROTATE_MAX:
            newRot = newRot - self.ROTATE_MAX

        while newRot < 0:
            newRot = newRot + self.ROTATE_MAX

        newRot = self.__roundAngle(newRot)

        self.__rotation = newRot
        self.__updateAgentRotType()


    def __updateAgentRotType(self):
        if (self.__rotation == 0):
            self.__currAgent = GridVals.ANT0
        elif(self.__rotation == 90):
            self.__currAgent = GridVals.ANT90
        elif(self.__rotation == 180):
            self.__currAgent = GridVals.ANT180
        elif(self.__rotation == 270):
            self.__currAgent = GridVals.ANT270

    def __roundAngle(self, x, base=ROTATE_ANGLE):
        return int(base * round(float(x) / base))

