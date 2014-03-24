from deap import algorithms, base, creator, tools
import random

from AgentNetwork import AgentNetwork
from AgentTrail import AgentTrail


NUM_MOVES = 100
POP_SIZE  = 300

def runMaze(individual):
    an = AgentNetwork()
    at = AgentTrail()
    at.readTrail("john_muir_32.yaml")

    an.network._setParameters(individual)

    for _ in xrange(NUM_MOVES):
        currMove = an.determineMove(at.isFoodAhead())

        if(currMove == 1):
            at.turnLeft()
        elif(currMove == 2):
            at.turnRight()
        elif(currMove == 3):
            at.moveForward()

    return (at.getFoodConsumed(),)


# Create the agent network and trail.
an = AgentNetwork()
at = AgentTrail()
at.readTrail("john_muir_32.yaml")

array = [1.5467588699829014, 2.891931908985611, 3.655295997731484, 2.5031662522667997, -1.1396741988880366, -0.4538713359287012, 3.4449290409464037, -4.785890055656329, -2.591732951545649, -3.990207915391867, -0.052707812828617584, -1.4075755280139965, -3.490825710706785, -2.943762218931295, -1.2255751047321661, -0.8102399924352195, 4.261394012128255, -2.6617903679899744, -4.485802686613816, 1.803215836221427, 2.275622299275904, 0.0, -4.746169134479325, 0.8366799597446297, 0.6395870506746721, -0.7081667054212097, -0.24269370584368488, -2.746352566533472, -2.800742700671044, 4.715347895101248, 4.909361860254416, 1.4257502715372414, -0.8473469896223147, 3.6657638240643884, 3.6318253430432605, 4.344961016216855, -2.6768520991404143, 1.8637167036836608, -4.943438448715291, -1.0845158747170416, -4.6038119993185775, -3.2993489137017162, 3.6200712737729717, 1.856473928872652, -3.361745319289322, 1.9582804333780466, -3.6046503305850797, 3.9935445224958865, 3.035268283729497, 4.0855797046760465, -4.997878677964618, 0.0, 2.5385363904010605, -0.6039546401363953, 2.8426040345063743, 2.1269142446158558, 4.070609433252875, -0.7630008522567246, 0.542951934561863, 0.0, 3.764499957254639, -4.143836393896326, -2.1672867653159535]
an.network._setParameters(array)

for _ in xrange(NUM_MOVES):
    currMove = an.determineMove(at.isFoodAhead())

    if(currMove == 1):
        at.turnLeft()
    elif(currMove == 2):
        at.turnRight()
    elif(currMove == 3):
        at.moveForward()

    print currMove

print at.getFoodConsumed()
at.printDataMatrix()

