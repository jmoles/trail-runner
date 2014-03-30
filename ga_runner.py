import argparse
from deap import algorithms, base, creator, tools
import json
import numpy as np
import os.path
import pickle
import random
import scoop
import zmq

from AgentNetwork import AgentNetwork
from AgentTrail import AgentTrail

# Configure DEAP
creator.create("FitnessMulti", base.Fitness, weights=(1,-1))
creator.create("Individual", list, fitness=creator.FitnessMulti)

def __singleMazeTask(individual, moves):
    an = AgentNetwork()
    at = AgentTrail()
    at.readTrail("trails/john_muir_32.yaml")

    num_moves = 0

    an.network._setParameters(individual)

    for _ in xrange(moves):
        # If all of the food is collected, done
        if at.getFoodStats()[1] == 0:
            break

        currMove = an.determineMove(at.isFoodAhead())

        if(currMove == 1):
            at.turnLeft()
        elif(currMove == 2):
            at.turnRight()
        elif(currMove == 3):
            at.moveForward()

        num_moves = num_moves + 1

    return (at.getFoodConsumed(), num_moves)

def main():
    # Configure ZMQ
    # Publisher role
    context   = zmq.Context()
    sender    = context.socket(zmq.PUSH)
    sender.bind("tcp://*:9854")

    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="Launches SCOOP parallelized version of genetic alogrithm.")
    parser.add_argument("-g", "--generations", type=int, nargs="?",
        default=200, help="Number of generations to run for.")
    parser.add_argument("-p", "--population", type=int, nargs="?",
        default=300, help="Size of the population.")
    parser.add_argument("-m", "--moves", type=int, nargs="?",
        default=300, help="Maximum moves for agent.")
    parser.add_argument("-c", "--checkpoint-file", type=str, nargs="?",
        help="Checkpoint file to load from last run.")

    args = parser.parse_args()

    an = AgentNetwork()

    toolbox = base.Toolbox()
    toolbox.register("map", scoop.futures.map)
    toolbox.register("attr_float", random.uniform, a=-5, b=5)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
        toolbox.attr_float, n=len(an.network.params))
    toolbox.register("population", tools.initRepeat, list,
        toolbox.individual)

    toolbox.register("evaluate", __singleMazeTask, moves=args.moves)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

    # Start a new evolution
    population = toolbox.population(n=args.population)
    start_gen  = 0
    halloffame = tools.HallOfFame(maxsize=1)
    food_stats = tools.Statistics(key=lambda ind: ind.fitness.values[0])
    move_stats = tools.Statistics(key=lambda ind: ind.fitness.values[1])
    mstats     = tools.MultiStatistics(food=food_stats, moves=move_stats)

    mstats.register("min", np.min)
    mstats.register("avg", np.mean)
    mstats.register("max", np.max)
    mstats.register("std", np.std)

    # Begin the generational process
    for gen in range(1, args.generations + 1):

        # TODO: Need to add check and comms from master
        # to cease work when the stop button is pushed.

        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))

        # Vary the pool of individuals
        offspring = algorithms.varAnd(offspring, toolbox, cxpb=0.5, mutpb=0.2)

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

        # Determinte the current generations statistics.
        record = mstats.compile(population)

        # Calculate the percent done for the progress bar.
        percent_done = int((float(gen) / float(args.generations)) * 100)

        if gen == args.generations:
            done = True
        else:
            done = False

        sender.send_json({
                "progress_percent"   : percent_done,
                "current_generation" : gen,
                "current_evals"      : len(invalid_ind),
                "top_dog"            : tools.selBest(population, k=1)[0],
                "done"               : done,
                "record"             : record})

if __name__ == "__main__":
    main()






