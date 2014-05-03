import argparse
from deap import algorithms, base, creator, tools
import json
import logging
import numpy as np
import os.path
import pickle
import random
import scoop
import socket
import string
import sys
import tables
import textwrap
import time
import uuid
import zmq

from AgentNetwork import AgentNetwork, NetworkTypes
from AgentTrail import AgentTrail
from  ProgressBar import *

# Configure DEAP
creator.create("FitnessMulti", base.Fitness, weights=(1,-1))
creator.create("Individual", list, fitness=creator.FitnessMulti)

# Configure Logging
root = logging.getLogger()
root.setLevel(logging.INFO)

# Pytables Stuff
FILTERS=tables.Filters(complevel=5, complib='zlib', fletcher32=True)

# Some constants
P_BIT_MUTATE = 0.05
TOURN_SIZE   = 3
P_MUTATE     = 0.2
P_CROSSOVER  = 0.5
WEIGHT_MIN   = -5.0
WEIGHT_MAX   = 5.0

# Class for table layout
class GAConf(tables.IsDescription):
    population_size    = tables.UInt16Col()
    max_moves          = tables.UInt16Col()
    num_gens           = tables.UInt16Col()
    date               = tables.Time32Col()
    uuid4              = tables.StringCol(len(str(uuid.uuid4())))
    runtime_sec        = tables.Time32Col()
    trail              = tables.StringCol(128)
    prob_mutate_bit    = tables.Float32Col()
    mutate_type        = tables.StringCol(32)
    prob_mutate        = tables.Float32Col()
    prob_crossover     = tables.Float32Col()
    tourn_size         = tables.UInt16Col()
    weight_min         = tables.Float32Col()
    weight_max         = tables.Float32Col()
    network            = tables.StringCol(64)
    hostname           = tables.StringCol(64)

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

        at = AgentTrail()
        at.readTrail(args.trail)

        row['population_size'] = args.population
        row['max_moves']       = args.moves
        row['num_gens']        = args.generations
        row['date']            = time_now
        row['uuid4']           = uuid_s
        row['network']         = network_s
        row['trail']           = at.getName()
        row['prob_mutate_bit'] = P_BIT_MUTATE
        row['mutate_type']     = "mutFlipBit"  # TODO: Update if type changes
        row['prob_mutate']     = P_MUTATE
        row['prob_crossover']  = P_CROSSOVER
        row['tourn_size']      = TOURN_SIZE
        row['weight_min']      = WEIGHT_MIN
        row['weight_max']      = WEIGHT_MAX
        row['hostname']        = socket.getfqdn()

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

def __recordRun(args, gen_i, runtime_i, uuid_s, moves_hof_i, food_hof_i, record_l, 
    hof_individual_npa=None):
    with tables.openFile(args.table_file, mode="a",
        filters=FILTERS) as fileh:
        indiv_table = fileh.getNode("/john_muir/run_stats")

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

        if hof_individual_npa is not None:
            tables_array = fileh.getNode("/john_muir/hof/" + uuid_s)
            tables_array.append(hof_individual_npa)

        row.append()
        indiv_table.flush()


def __singleMazeTask(individual, moves, trail, network_type):
    an = AgentNetwork(network_type)
    at = AgentTrail()
    at.readTrail(trail)

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
    # Build some data for arguments output.
    network_types_s = ""
    network_num   = 0
    for curr_s in NetworkTypes.STRINGS:
        network_types_s += "\t" + str(network_num) + ":" + curr_s + "\n"
        network_num += 1

    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="Launches SCOOP parallelized version "
        "of genetic alogrithm.",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-g", "--generations", type=int, nargs="?",
        default=200, help="Number of generations to run for.")
    parser.add_argument("-p", "--population", type=int, nargs="?",
        default=300, help="Size of the population.")
    parser.add_argument("-m", "--moves", type=int, nargs="?",
        default=325, help="Maximum moves for agent.")
    parser.add_argument("-n", "--network", type=int, nargs="?",
        default=1,
        help=textwrap.dedent("Network type to use. Valid options are:\n" + 
            network_types_s),
        choices=range(0,len(NetworkTypes.STRINGS)))
    parser.add_argument("-t", "--trail", type=str, nargs="?",
        default="trails/john_muir_32.yaml", help="Trail file to read.")
    parser.add_argument("-z", "--enable-zmq-updates", action='store_true',
        help="Enable use of ZMQ messaging for real-time GUI monitoring.")
    parser.add_argument("-f", "--table-file", type=str,
        nargs="?",
        help="File to save table data in.")
    parser.add_argument("-r", "--repeat", type=int, nargs="?",
        default=1, help="Number of times to run simulations.")
    args = parser.parse_args()

    if not args.table_file:
        logging.warning("No table file was specified. These runs will "
            "not get recorded in the logging database.")
        time.sleep(3)

    run_date = time.time()

    term = TerminalController()
    try:
        progress = ProgressBar(term, 'Running Genetic Algorithm')
    except ValueError:
        logging.warning("Unable to use ProgressBar on this platform.")
        progress = None

    for curr_repeat in range(0, args.repeat):

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
        toolbox.register("attr_float", random.uniform, a=WEIGHT_MIN, b=WEIGHT_MAX)
        toolbox.register("individual", tools.initRepeat, creator.Individual,
            toolbox.attr_float, n=len(AgentNetwork(args.network).network.params))
        toolbox.register("population", tools.initRepeat, list,
            toolbox.individual)

        toolbox.register("evaluate", __singleMazeTask, moves=args.moves,
            trail=args.trail, network_type=args.network)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutFlipBit, indpb=P_BIT_MUTATE)
        toolbox.register("select", tools.selTournament, tournsize=TOURN_SIZE)

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

        if args.table_file != None:
            __prepareTable(args, time.time(), uuid_str,
                AgentNetwork(args.network).getStringName(), AgentNetwork(args.network).getParamsLength())

        # Begin the generational process
        for gen in range(1, args.generations + 1):

            gen_start_time = time.time()

            # TODO: Need to add check and comms from master
            # to cease work when the stop button is pushed.

            # Select the next generation individuals
            offspring = toolbox.select(population, len(population))

            # Vary the pool of individuals
            offspring = algorithms.varAnd(offspring, toolbox,
                cxpb=P_CROSSOVER, mutpb=P_MUTATE)

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
                args.moves, args.trail, args.network)

            # Record data in the table.
            if args.table_file != None:
                __recordRun(args, gen, time.time() - gen_start_time,
                    uuid_str, this_moves, this_food, record,
                    np.array(tools.selBest(population, k=1)[0], ndmin=2))

            # Update the progress bar
            if progress:
                bar_done_val = ((float(percent_done) / (100.0 * args.repeat)) +
                    (float(curr_repeat)) / (float(args.repeat)))
                progress.update(bar_done_val,
                    "on generation %d / %d of repeat %d / %d" % (gen,
                        args.generations, curr_repeat + 1, args.repeat))
            else:
                logging.info("on generation %d / %d of repeat %d / %d" % (gen,
                        args.generations, curr_repeat + 1, args.repeat))

    # Update the run configuration with total runtime
    total_time_s = time.time() - run_date
    if args.table_file != None:
        __updateRuntime(args, uuid_str, total_time_s)


    logging.info("Run completed in " +
        time.strftime('%H:%M:%S', time.gmtime(total_time_s)) + ".")


if __name__ == "__main__":
    main()






