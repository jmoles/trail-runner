from deap import algorithms, base, creator, tools
import numpy as np
import os.path
import pickle
import random
import timeit
from PySide import QtCore, QtGui

from AgentNetwork import AgentNetwork
from AgentTrail import AgentTrail

# Configure DEAP
creator.create("FitnessMax", base.Fitness, weights=(100.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

class Communicate(QtCore.QObject):
    newProg       = QtCore.Signal(int)
    newIndividual = QtCore.Signal(list)

class AgentGA(QtCore.QThread):

    CHECKPOINT = "checkpoint.pkl"
    PICKLE_VER = 1

    def __init__(self, bar=None):
        super(AgentGA, self).__init__()

        self.an         = AgentNetwork()

        self.toolbox    = base.Toolbox()

        self.filename   = ""
        self.moves      = 0
        self.pop_size   = 0
        self.gens       = 0

        # Current generation evaluation is on.
        self.curr_gen   = 0

        # Set up the toolbox.
        self.__initToolbox()

        # Communicate class
        self.c          = Communicate()

        self.bar        = bar

        # Variable to indicate if the loop should continue running.
        self.__abort      = False

        # Connect the signal/slot for the progress bar
        self.c.newProg[int].connect(self.bar.setValue)

    def setVars(self, filename, moves, pop, gens):
        self.filename   = filename
        self.moves      = moves
        self.pop_size   = pop
        self.gens       = gens

    def run(self):
        self.__abort = False
        self.__runMaze(AgentGA.CHECKPOINT)

    def stop(self):
        self.__abort = True
        self.wait()

    def __initToolbox(self):
        self.toolbox.register("attr_float", random.uniform, a=-5, b=5)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual,
            self.toolbox.attr_float, n=len(self.an.network.params))
        self.toolbox.register("population", tools.initRepeat, list,
            self.toolbox.individual)

        self.toolbox.register("evaluate", self.__singleMazeTask)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=3)


    def __runMaze(self, checkpoint=None):
        pickleread = False

        # TODO: Pickling needs to check paramters for maze too before accepting
        # the use of pickled data.
        if checkpoint and os.path.isfile(checkpoint):
            # A file name has been given, then load the data from the file
            cp         = pickle.load(open(checkpoint, "r"))
            version    = cp["version"]

            if version == AgentGA.PICKLE_VER:
                population = cp["population"]
                start_gen  = cp["generation"]
                halloffame = cp["halloffame"]
                logbook    = cp["logbook"]
                random.setstate(cp["rndstate"])
                pickleread = True

        if not pickleread:
            # Start a new evolution
            population = self.toolbox.population(n=self.pop_size)
            start_gen  = 0
            halloffame = tools.HallOfFame(maxsize=1)
            logbook    = tools.Logbook()
            version    = AgentGA.PICKLE_VER 

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("max", np.max)

        for gen in range(start_gen, self.gens):
            population = algorithms.varAnd(population, self.toolbox, cxpb=0.5, mutpb=0.2)

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in population if not ind.fitness.valid]
            fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            halloffame.update(population)
            record = stats.compile(population)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)

            population = self.toolbox.select(population, k=len(population))

            self.curr_gen = gen

            if gen % 1 == 0:
                # Fill the dictionary using the dict(key=value[, ...]) constructor
                cp = dict(population=population, generation=gen, halloffame=halloffame,
                          logbook=logbook, rndstate=random.getstate(), version=version)
                pickle.dump(cp, open(AgentGA.CHECKPOINT, "w"))

            print str(int((float(gen + 1) / float(self.gens)) * 100))
            self.c.newProg.emit(int((float(gen + 1) / float(self.gens)) * 100))

            if(self.__abort):
                break

        print(tools.selBest(population, k=1)[0])
        self.c.newIndividual.emit(tools.selBest(population, k=1)[0])


    def __singleMazeTask(self, individual):
        an = AgentNetwork()
        at = AgentTrail()
        at.readTrail("trails/john_muir_32.yaml")

        an.network._setParameters(individual)

        for _ in xrange(self.moves):
            currMove = an.determineMove(at.isFoodAhead())

            if(currMove == 1):
                at.turnLeft()
            elif(currMove == 2):
                at.turnRight()
            elif(currMove == 3):
                at.moveForward()

        return (at.getFoodConsumed(),)

