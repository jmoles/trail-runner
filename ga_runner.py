import argparse
import datetime
from deap import algorithms, base, creator, tools
import json
import logging
import numpy as np
import os
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

from AgentNetwork import AgentNetwork, NetworkTypes
from AgentTrail import AgentTrail
from DBUtils import DBUtils

try:
    import progressbar
except ImportError:
    logging.warning("progressbar2 library is not available. " +
        "Try 'pip install progressbar2'")

# Configure DEAP
creator.create("FitnessMulti", base.Fitness, weights=(1,-1))
creator.create("Individual", list, fitness=creator.FitnessMulti)

# Some constants
P_BIT_MUTATE = 0.05
TOURN_SIZE   = 3
P_MUTATE     = 0.2
P_CROSSOVER  = 0.5
WEIGHT_MIN   = -5.0
WEIGHT_MAX   = 5.0

def __recordSingleRun(tp, run_id, gen_i, runtime_i, moves_hof_i,
    food_hof_i, record_l, hof_individual_npa, moves_stats_i):

    record_info = {}



def __singleMazeTask(individual, moves, trail, network_type,
    stats_run = False):
    an = AgentNetwork(network_type)
    at = AgentTrail()
    at.readTrail(trail)

    num_moves = 0

    an.network._setParameters(individual)

    move_stats            = {}
    move_stats["none"]    = 0
    move_stats["left"]    = 0
    move_stats["right"]   = 0
    move_stats["forward"] = 0

    for _ in xrange(moves):
        # If all of the food is collected, done
        if at.getFoodStats()[1] == 0:
            break

        currMove = an.determineMove(at.isFoodAhead())

        if(currMove == 1):
            at.turnLeft()
            move_stats["left"] += 1
        elif(currMove == 2):
            at.turnRight()
            move_stats["right"] += 1
        elif(currMove == 3):
            at.moveForward()
            move_stats["forward"] += 1
        else:
            move_stats["none"] += 1

        num_moves += 1

    if stats_run:
        return (at.getFoodConsumed(), num_moves, move_stats)
    else:
        return (at.getFoodConsumed(), num_moves)

def main():
    # Query the database to gather some items for argument output.
    pgdb = DBUtils(password=os.environ['PSYCOPG2_DB_PASS'])

    network_types_s, valid_net_opts = pgdb.fetchNetworkCmdPrettyPrint()
    trail_types_s, valid_trail_opts = pgdb.fetchTrailList()

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
        choices=valid_net_opts)
    parser.add_argument("-t", "--trail", type=str, nargs="?",
        default="trails/john_muir_32.yaml", help="Trail file to read.")
    parser.add_argument("-z", "--enable-zmq-updates", action='store_true',
        help="Enable use of ZMQ messaging for real-time GUI monitoring.")
    parser.add_argument("-r", "--repeat", type=int, nargs="?",
        default=1, help="Number of times to run simulations.")
    parser.add_argument("--disable-db",
        action='store_true')
    parser.add_argument("--debug",
        action='store_true',
        help="Enables debug messages and flag for data in DB.")
    parser.add_argument("-q", "--quiet", action='store_true')
    args = parser.parse_args()

    run_date = time.time()

    # Configure Logging
    root = logging.getLogger()
    if(args.debug):
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)

    if args.quiet:
        root.propogate = False

    # Get the name of this agent trail for later use
    at = AgentTrail()
    at.readTrail(args.trail)
    trail_name = at.getName()

    if not args.quiet:
        try:
            widgets = ['Processed: ', progressbar.Percentage(), ' ',
                progressbar.Bar(marker=progressbar.RotatingMarker()),
                ' ', progressbar.ETA()]
            pbar = progressbar.ProgressBar(widgets=widgets, maxval=100).start()
        except:
            pbar = None
    else:
        pbar = None

    for curr_repeat in range(0, args.repeat):
        repeat_start_time = datetime.datetime.now()


        if not args.disable_db:
            # Create a tuple to store stats
            gens_stat_list = []

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

        # Record the start of this run.
        if not args.disable_db:
            log_time = datetime.datetime.now()

        # Begin the generational process
        for gen in range(1, args.generations + 1):

            gen_start_time = datetime.datetime.now()

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

            # Determine the current generations statistics.
            record = mstats.compile(population)

            print record

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

            if not args.disable_db:
                # Record the statistics for this run.
                _, _, this_move_stats = (
                __singleMazeTask(tools.selBest(
                population, k=1)[0],
                args.moves, args.trail, args.network, True))

                record_info                  = {}
                record_info["gen"]           = gen - 1
                record_info["runtime"]       = (datetime.datetime.now() -
                        gen_start_time)
                record_info["food_max"]      = record["food"]["max"]
                record_info["food_min"]      = record["food"]["min"]
                record_info["food_avg"]      = record["food"]["avg"]
                record_info["food_std"]      = record["food"]["std"]
                record_info["moves_max"]     = record["moves"]["max"]
                record_info["moves_min"]     = record["moves"]["min"]
                record_info["moves_avg"]     = record["moves"]["avg"]
                record_info["moves_std"]     = record["moves"]["std"]
                record_info["moves_left"]    = this_move_stats["left"]
                record_info["moves_right"]   = this_move_stats["right"]
                record_info["moves_forward"] = this_move_stats["forward"]
                record_info["moves_none"]    = this_move_stats["none"]
                record_info["elite"]         = np.array(
                        tools.selBest(population, k=1)[0]).tolist()

                gens_stat_list.append(record_info)



            hof_array[gen - 1] = np.array(tools.selBest(population, k=1)[0])

            # Update the progress bar
            if pbar:
                bar_done_val = ((float(percent_done) / (100.0 * args.repeat)) +
                    (float(curr_repeat)) / (float(args.repeat)))
                pbar.update(bar_done_val * 100)
            else:
                logging.info("on generation %d / %d of repeat %d / %d" % (gen,
                        args.generations, curr_repeat + 1, args.repeat))

        # Record the statistics on this run.
        if not args.disable_db:
            run_info = {}

            run_info["trails_id"]    = 3
            run_info["networks_id"]  = args.network
            run_info["mutate_id"]    = 1 # Only one type of mutate for now.
            run_info["host_type_id"] = 1 # Only one host type for now.
            run_info["run_date"]     = log_time
            run_info["hostname"]     = socket.getfqdn()
            run_info["generations"]  = args.generations
            run_info["population"]   = args.population
            run_info["moves_limit"]  = args.moves
            run_info["elite_count"]  = TOURN_SIZE
            run_info["p_mutate"]     = P_MUTATE
            run_info["p_crossover"]  = P_CROSSOVER
            run_info["weight_min"]   = WEIGHT_MIN
            run_info["weight_max"]   = WEIGHT_MAX
            run_info["debug"]        = args.debug
            run_info["runtime"]      = (datetime.datetime.now() -
                repeat_start_time)

            pgdb.recordRun(run_info, gens_stat_list)


    # Calculate and display the total runtime
    if pbar:
        pbar.finish()
    total_time_s = time.time() - run_date

    logging.info("Run completed in " +
        time.strftime('%H:%M:%S', time.gmtime(total_time_s)) + ".")


if __name__ == "__main__":
    main()






