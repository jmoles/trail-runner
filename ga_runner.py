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
import textwrap
import time
import uuid
import zmq

import pandas as pd

from AgentNetwork import AgentNetwork, NetworkTypes
from AgentTrail import AgentTrail
from  ProgressBar import *

# Configure DEAP
creator.create("FitnessMulti", base.Fitness, weights=(1,-1))
creator.create("Individual", list, fitness=creator.FitnessMulti)

# Configure Logging
root = logging.getLogger()
root.setLevel(logging.INFO)

# Some constants
P_BIT_MUTATE = 0.05
TOURN_SIZE   = 3
P_MUTATE     = 0.2
P_CROSSOVER  = 0.5
WEIGHT_MIN   = -5.0
WEIGHT_MAX   = 5.0

def __recordSingleRun(df, gen_i, runtime_i, moves_hof_i, food_hof_i, record_l, 
    hof_individual_npa=None):

    df.iloc[gen_i-1,:]=[
        runtime_i,
        moves_hof_i,
        food_hof_i,
        record_l["food"]["min"],
        record_l["food"]["avg"],
        record_l["food"]["max"],
        record_l["food"]["std"],
        record_l["moves"]["min"],
        record_l["moves"]["avg"],
        record_l["moves"]["max"],
        record_l["moves"]["std"]
    ]

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
    parser.add_argument("-r", "--repeat", type=int, nargs="?",
        default=1, help="Number of times to run simulations.")
    parser.add_argument("--data-dir", type=str, nargs="?",
        default="data", help="Data directory.")
    parser.add_argument("--disable-logging",
        action='store_true')
    args = parser.parse_args()

    run_date = time.time()

    # Check if data directories exist and sanatize name.
    if not args.disable_logging:
        if not os.path.isdir(args.data_dir):
            logging.critical("Specified data directory does not exist.")
            sys.exit(1)

        data_dir = os.path.normpath(args.data_dir) + "/"

        # Create the runs directory in data if it doesn't exist.
        if not os.path.isdir(data_dir + "runs"):
            os.mkdir(data_dir + "runs")

    # Get the name of this agent trail for later use
    at = AgentTrail()
    at.readTrail(args.trail)
    trail_name = at.getName()

    term = TerminalController()
    try:
        progress = ProgressBar(term, 'Running Genetic Algorithm')
    except ValueError:
        logging.warning("Unable to use ProgressBar on this platform.")
        progress = None

    df_single = pd.DataFrame(np.random.randn(args.generations,11), columns=[
            'runtime_s', 'hof_moves', 'hof_food', 
            'food_min', 'food_avg', 'food_max', 'food_std',
            'moves_min', 'moves_avg', 'moves_max', 'moves_std'])

    best_food = 0
    best_moves = sys.maxint

    for curr_repeat in range(0, args.repeat):
        repeat_start_time = time.time()

        # Prepare the array for storing hall of fame.
        hof_array = np.zeros((args.generations, 
            AgentNetwork(args.network).getParamsLength()))

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

            # Store and update statistics.
            __recordSingleRun(df_single, gen, time.time() - gen_start_time,
                this_moves, this_food, record)

            hof_array[gen - 1] = np.array(tools.selBest(population, k=1)[0])

            if this_food > best_food:
                best_food = this_food

            if this_moves < best_moves:
                best_moves = this_moves

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

        # Record the statistics on this run.
        if not args.disable_logging:
            store_fname = (data_dir + "runs/" +
                time.strftime("%Y%m%d_%H%M%S") + ".h5")
            store = pd.HDFStore(store_fname, complib='zlib', complevel=9)
            store['gens'] = df_single
            store['hof']  = pd.DataFrame(hof_array)
            store.close()

            try:
                df_summary = pd.read_csv(data_dir + "summary.csv")
                next_idx = max(df_summary.index) + 1
                do_header = False
            except:
                next_idx = 0
                do_header = True

            with open('data/summary.csv', 'a') as fileh:
                pd.DataFrame({
                    'run_date'     : pd.Timestamp.now(),
                    'pop_size'     : args.population,
                    'max_moves'    : args.moves,
                    'gen_count'    : args.generations,
                    'runtime_s'    : time.time() - repeat_start_time,
                    'trail_file'   : trail_name,
                    'p_mutate_bit' : P_BIT_MUTATE,
                    'mutate_type'  : "mutFlipBit", #TODO: Update if this type changes.
                    'p_mutate'     : P_MUTATE,
                    'p_crossover'  : P_CROSSOVER,
                    'tourn_size'   : TOURN_SIZE,
                    'weight_min'   : WEIGHT_MIN,
                    'weight_max'   : WEIGHT_MAX,
                    'network_name' : AgentNetwork(args.network).getStringName(),
                    'hostname'     : socket.getfqdn(),
                    'max_food'     : best_food,
                    'min_moves'    : best_moves
                }, index=[next_idx]).to_csv(fileh, header=do_header)


    # Calculate and display the total runtime
    total_time_s = time.time() - run_date

    logging.info("Run completed in " +
        time.strftime('%H:%M:%S', time.gmtime(total_time_s)) + ".")


if __name__ == "__main__":
    main()






