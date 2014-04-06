import argparse
from deap import algorithms, base, creator, tools
import json
import logging
import numpy as np
import os.path
import pickle
import random
import scoop
import string
import sys
import tables
import time
import uuid
import zmq

from AgentNetwork import AgentNetwork
from AgentTrail import AgentTrail

# Configure DEAP
creator.create("FitnessMulti", base.Fitness, weights=(1,-1))
creator.create("Individual", list, fitness=creator.FitnessMulti)

# Configure Logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Pytables Stuff
FILTERS=tables.Filters(complevel=5, complib='zlib', fletcher32=True)

# Class for table layout
class GAConf(tables.IsDescription):
    population_size    = tables.UInt16Col()
    max_moves          = tables.UInt16Col()
    num_gens           = tables.UInt16Col()
    date               = tables.Time32Col()
    uuid4              = tables.StringCol(len(str(uuid.uuid4())))
    runtime_sec        = tables.Time32Col()
    network            = tables.StringCol(64)

class GARun(tables.IsDescription):
    generation         = tables.UInt16Col()
    runtime_sec        = tables.UInt32Col()
    uuid4              = tables.StringCol(len(str(uuid.uuid4())))
    moves_hof          = tables.UInt16Col()
    food_hof           = tables.UInt16Col()
    food_min           = tables.UInt16Col()
    food_avg           = tables.UInt16Col()
    food_max           = tables.UInt16Col()
    food_std           = tables.UInt16Col()
    moves_min          = tables.UInt16Col()
    moves_avg          = tables.UInt16Col()
    moves_max          = tables.UInt16Col()
    moves_std          = tables.UInt16Col()

def __prepareTable(args, time_now, uuid_s, network_s, params_len):
    # Record the configuration for this run.
    with tables.openFile(args.table_file, mode="a",
        filters=FILTERS) as fileh:
        try:
            fileh.getNode("/john_muir")
        except tables.NoSuchNodeError:
            logging.debug("Creating /join_muir group....")
            fileh.createGroup("/", 'john_muir',
                'John Muir (Jefferson) Trail')

        try:
            conf_table = fileh.getNode("/john_muir/run_conf")
        except tables.NoSuchNodeError:
            logging.debug(
                "Creating /john_muir/run_conf table...")
            conf_table = fileh.createTable("/john_muir/",
                "run_conf", GAConf)

        row = conf_table.row

        row['population_size'] = args.population
        row['max_moves']       = args.moves
        row['num_gens']        = args.generations
        row['date']            = time_now
        row['uuid4']           = uuid_s
        row['network']         = network_s

        row.append()
        conf_table.flush()

        # Do some checking prior to entering loop.
        try:
            fileh.getNode("/john_muir/run_stats")
        except tables.NoSuchNodeError:
            logging.debug(
                "Creating /john_muir/run_stats table...")
            fileh.createTable("/john_muir/", "run_stats", GARun)

        try:
            fileh.getNode("/john_muir/hof")
        except tables.NoSuchNodeError:
            logging.debug(
                "Creating /john_muir/hof group...")
            fileh.createGroup("/john_muir/", "hof",
                "Hall of Fame for Runs")

        try:
            fileh.getNode("/john_muir/hof/" + uuid_s)
        except tables.NoSuchNodeError:
            logging.debug("Creating new hall of fame array for " +
                uuid_s + ".")
            fileh.createEArray("/john_muir/hof/",
                name = uuid_s,
                atom = tables.Float64Col(),
                shape = (0, params_len),
                expectedrows = args.generations)

def __updateRuntime(args, uuid_s, runtime_i):
    with tables.openFile(args.table_file, mode="a",
        filters=FILTERS) as fileh:
            conf_table = fileh.root.john_muir.run_conf
            index = conf_table.getWhereList('uuid4=="' + uuid_s + '"')[0]
            conf_table.cols.runtime_sec[index] = runtime_i
            conf_table.flush()

def __recordRun(args, gen_i, runtime_i, uuid_s, moves_hof_i, food_hof_i, record_l, hof_individual_npa):
    with tables.openFile(args.table_file, mode="a",
        filters=FILTERS) as fileh:
        indiv_table = fileh.getNode("/john_muir/run_stats")
        tables_array = fileh.getNode("/john_muir/hof/" + uuid_s)

        row = indiv_table.row

        row['generation']  = gen_i
        row['runtime_sec'] = runtime_i
        row['uuid4']       = uuid_s
        row['moves_hof']   = moves_hof_i
        row['food_hof']    = food_hof_i
        row['food_min']    = record_l["food"]["min"]
        row['food_avg']    = record_l["food"]["avg"]
        row['food_max']    = record_l["food"]["max"]
        row['food_std']    = record_l["food"]["std"]
        row['moves_min']   = record_l["moves"]["min"]
        row['moves_avg']   = record_l["moves"]["avg"]
        row['moves_max']   = record_l["moves"]["max"]
        row['moves_std']   = record_l["moves"]["std"]
        tables_array.append(hof_individual_npa)

        row.append()
        indiv_table.flush()


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
    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="Launches SCOOP parallelized version of genetic alogrithm.")
    parser.add_argument("-g", "--generations", type=int, nargs="?",
        default=200, help="Number of generations to run for.")
    parser.add_argument("-p", "--population", type=int, nargs="?",
        default=300, help="Size of the population.")
    parser.add_argument("-m", "--moves", type=int, nargs="?",
        default=325, help="Maximum moves for agent.")
    parser.add_argument("-c", "--checkpoint-file", type=str, nargs="?",
        help="Checkpoint file to load from last run.")
    parser.add_argument("-z", "--enable-zmq-updates", action='store_true',
        help="Enable use of ZMQ messaging for real-time GUI monitoring.")
    parser.add_argument("-t", "--table-file", type=str,
        nargs="?", default="data.h5",
        help="File to save table data in.")
    parser.add_argument("-r", "--repeat", type=int, nargs="?",
        default=1, help="Number of times to run simulations.")
    args = parser.parse_args()

    run_date = time.time()

    for _ in range(0, args.repeat):

        if(args.enable_zmq_updates):
            # Configure ZMQ - Publisher role
            context   = zmq.Context()
            sender    = context.socket(zmq.PUSH)
            sender.bind("tcp://*:9854")

        uuid_str = list(str(uuid.uuid4()).replace("-",""))
        uuid_str[0] = random.choice(string.letters)
        uuid_str = "".join(uuid_str)


        toolbox = base.Toolbox()
        toolbox.register("map", scoop.futures.map)
        toolbox.register("attr_float", random.uniform, a=-5, b=5)
        toolbox.register("individual", tools.initRepeat, creator.Individual,
            toolbox.attr_float, n=len(AgentNetwork().network.params))
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

        __prepareTable(args, run_date, uuid_str,
            AgentNetwork().getStringName(), AgentNetwork().getParamsLength())

        # Begin the generational process
        for gen in range(1, args.generations + 1):

            gen_start_time = time.time()

            # TODO: Need to add check and comms from master
            # to cease work when the stop button is pushed.

            # Select the next generation individuals
            offspring = toolbox.select(population, len(population))

            # Vary the pool of individuals
            offspring = algorithms.varAnd(offspring, toolbox,
                cxpb=0.5, mutpb=0.2)

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

            if(args.enable_zmq_updates):
                sender.send_json({
                        "progress_percent"   : percent_done,
                        "current_generation" : gen,
                        "current_evals"      : len(invalid_ind),
                        "top_dog"            : tools.selBest(
                            population, k=1)[0],
                        "done"               : done,
                        "record"             : record})

            this_food, this_moves = __singleMazeTask(tools.selBest(
                population, k=1)[0],
                args.moves)

            # Record data in the table.
            __recordRun(args, gen, time.time() - gen_start_time,
                uuid_str, this_moves, this_food, record,
                np.array(tools.selBest(population, k=1)[0], ndmin=2))


    # Update the run configuration with total runtime
    total_time_s = time.time() - run_date
    __updateRuntime(args, uuid_str, total_time_s)


    logging.info("Run " + uuid_str + " completed in " +
        time.strftime('%H:%M:%S', time.gmtime(total_time_s)) + ".")


if __name__ == "__main__":
    main()






