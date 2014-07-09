""" Runs evolution on a delay line. """

from deap import algorithms, base, creator, tools
from GATools.chemistry import DelayLine
import numpy as np
import random
import scoop
import time

DL_LENGTH = 2
DL_ITER = 10
WEIGHT_MIN = 0.0
WEIGHT_MAX = 1.0
POP_SIZE = 150
GENERATIONS = 10000
TEST_VECTOR = abs(np.random.randn(10))

PXOR = 0.5
PMUT = 0.2

PARAMS_LEN = DL_LENGTH * 3

# Configure DEAP
creator.create("FitnessMulti", base.Fitness, weights=(-1.0, ) * DL_LENGTH)
creator.create("Individual", list, fitness=creator.FitnessMulti)

def evaluate(individual):
    indiv_a = abs(np.array(individual))
    indiv_reshape = indiv_a.reshape(len(indiv_a) / 3, 3)

    this_delay_line = DelayLine(rate_constants=indiv_reshape,
        user_interactive=False)
    for item in TEST_VECTOR:
        res = this_delay_line.evaluate(item)

    return abs(
        (res - this_delay_line.ideal_values)
        / this_delay_line.ideal_values)


def main():


    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.uniform,
        a=WEIGHT_MIN, b=WEIGHT_MAX)
    toolbox.register("map", scoop.futures.map)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.attr_float, n=PARAMS_LEN)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)
    toolbox.register("select", tools.selTournament, tournsize=15)
    toolbox.register("evaluate", evaluate)

    population = toolbox.population(n=POP_SIZE)
    halloffame = tools.HallOfFame(maxsize=1)

    # Begin the generational process
    for gen in range(0, GENERATIONS):

        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))

        # Vary the pool of individuals
        offspring = algorithms.varAnd(offspring, toolbox,
            cxpb=PXOR, mutpb=PMUT)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)

        # Replace the current population by the offspring
        population[:] = offspring

    return np.array(tools.selBest(population, k=1)[0]).tolist()



if __name__ == "__main__":
    run_date = time.time()

    individual = main()

    indiv_a = abs(np.array(individual))
    indiv_reshape = indiv_a.reshape(len(indiv_a) / 3, 3)

    this_delay_line = DelayLine(rate_constants=indiv_reshape, user_interactive=True)

    for item in TEST_VECTOR:
        print "Running " + str(item)
        res = this_delay_line.evaluate(item)

    print "Error is " + str(abs(
        (res - this_delay_line.ideal_values)
        / this_delay_line.ideal_values)) + "."

    print "Individual is " + str(indiv_reshape) + "."

    total_time_s = time.time() - run_date

    print "Run completed in {0}.".format(time.strftime('%H:%M:%S',
        time.gmtime(total_time_s)))

    this_delay_line.show_plot()

