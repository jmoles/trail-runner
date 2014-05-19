from scipy import * #@UnusedWildImport
import pylab

from pybrain.rl.environments.mazes import Maze, MDPMazeTask
from pybrain.rl.learners.valuebased import ActionValueTable
from pybrain.rl.agents import LearningAgent
from pybrain.rl.learners import Q, SARSA #@UnusedImport
from pybrain.rl.experiments import Experiment


pylab.gray()
pylab.ion()


structure = array([[1, 1, 1, 1, 1, 1, 1, 1, 1],
                   [1, 0, 0, 1, 0, 0, 0, 0, 1],
                   [1, 0, 0, 1, 0, 0, 1, 0, 1],
                   [1, 0, 0, 1, 0, 0, 1, 0, 1],
                   [1, 0, 0, 1, 0, 1, 1, 0, 1],
                   [1, 0, 0, 0, 0, 0, 1, 0, 1],
                   [1, 1, 1, 1, 1, 1, 1, 0, 1],
                   [1, 0, 0, 0, 0, 0, 0, 0, 1],
                   [1, 1, 1, 1, 1, 1, 1, 1, 1]])


environment = Maze(structure, (7, 7))



controller = ActionValueTable(81, 4)
controller.initialize(1.)



learner = Q()
agent = LearningAgent(controller, learner)


task = MDPMazeTask(environment)

experiment = Experiment(task, agent)

while True:
    experiment.doInteractions(100)
    agent.learn()
    agent.reset()
    pylab.pcolor(controller.params.reshape(81,4).max(1).reshape(9,9))
    pylab.draw()
