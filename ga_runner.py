import argparse
import datetime
from deap import algorithms, base, creator, tools
import json
import logging
import numpy as np
import os
import pickle
import random
import re
import scoop
import socket
import sys
import tempfile
import textwrap
import time
import zmq

from GATools.trail.network import network as AgentNetwork
from GATools.trail.trail import trail as AgentTrail
from GATools.DBUtils import DBUtils

try:
    import progressbar
except ImportError:
    logging.warning("progressbar2 library is not available. " +
        "Try 'pip install progressbar2'")

# Configure DEAP
creator.create("FitnessMulti", base.Fitness, weights=(1.0,-0.1))
creator.create("Individual", list, fitness=creator.FitnessMulti)

# Some constants
P_BIT_MUTATE    = 0.05
GENS_DEF        = 200
POP_DEF         = 300
MOVES_DEF       = 200
ELITE_COUNT_DEF = 3
P_MUTATE_DEF    = 0.2
P_CROSSOVER_DEF = 0.5
WEIGHT_MIN_DEF  = -5.0
WEIGHT_MAX_DEF  = 5.0

def __singleMazeTask(individual, moves, trail_matrix, trail_name, trail_rot,
    pb_filename, detailed_stats=False):
    an = AgentNetwork()
    an.readNetworkFromFile(pb_filename)
    at = AgentTrail()
    at.readTrailInstant(trail_matrix, trail_name, trail_rot)

    an.updateParameters(individual)

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
        else:
            at.noMove()

    if detailed_stats == True:
        return (at.getFoodConsumed(), at.getNumMoves(), at.getMovesStats())
    else:
        return (at.getFoodConsumed(), at.getNumMoves())

def main():
    # Query the database to gather some items for argument output.
    pgdb = DBUtils(password=os.environ['PSYCOPG2_DB_PASS'])

    network_types_s, valid_net_opts = pgdb.fetchNetworkCmdPrettyPrint()
    trail_types_s, valid_trail_opts = pgdb.fetchTrailList()

    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="Launches SCOOP parallelized version "
        "of genetic algorithm.",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-g", "--generations", type=int, nargs="?",
        default=GENS_DEF,
        help="Number of generations to run for.")
    parser.add_argument("-p", "--population", type=int, nargs="?",
        default=POP_DEF,
        help="Size of the population.")
    parser.add_argument("-m", "--moves", type=int, nargs="?",
        default=MOVES_DEF,
        help="Maximum moves for agent.")
    parser.add_argument("-n", "--network", type=int, nargs="?",
        default=1,
        help=textwrap.dedent("Network type to use. Valid options are:\n" +
            network_types_s),
        choices=valid_net_opts)
    parser.add_argument("-t", "--trail", type=int, nargs="?",
        default=3,
        help=textwrap.dedent(
            "Trail to use. Valid options (with recommended moves) are:\n" +
            trail_types_s),
        choices=valid_trail_opts)

    parser.add_argument("--prob-mutate", type=float, nargs="?",
        default=P_MUTATE_DEF,
        help="Probability of a mutation to occur.")
    parser.add_argument("--prob-crossover", type=float, nargs="?",
        default=P_CROSSOVER_DEF,
        help="Probability of crossover to occur.")
    parser.add_argument("--weight-min", type=float, nargs="?",
        default=WEIGHT_MIN_DEF,
        help="Minimum weight.")
    parser.add_argument("--weight-max", type=float, nargs="?",
        default=WEIGHT_MAX_DEF,
        help="Maximum weight")
    parser.add_argument("--elite-count", type=int, nargs="?",
        default=ELITE_COUNT_DEF,
        help="Number of elites taken after each generation.")

    parser.add_argument("-z", "--enable-zmq-updates", action='store_true',
        help="Enable use of ZMQ messaging for real-time GUI monitoring.")
    parser.add_argument("-r", "--repeat", type=int, nargs="?",
        default=1, help="Number of times to run simulations.")
    parser.add_argument("--disable-db",
        action='store_true',
        help="Disables logging of run to database.")
    parser.add_argument("--debug",
        action='store_true',
        help="Enables debug messages and flag for data in DB.")
    parser.add_argument("-q", "--quiet",
        action='store_true',
        help="Disables all output from application.")
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

    if args.weight_min > args.weight_max:
        logging.critical("Minimum weight must be greater than max weight.")
        sys.exit(1)

    # Get the name of this agent trail for later use
    at = AgentTrail()
    at.readTrail(args.trail)
    trail_name = at.getName()

    if not args.quiet and not args.debug:
        try:
            widgets = ['Processed: ', progressbar.Percentage(), ' ',
                progressbar.Bar(marker=progressbar.RotatingMarker()),
                ' ', progressbar.ETA()]
            pbar = progressbar.ProgressBar(widgets=widgets, maxval=100).start()
        except:
            pbar = None
    else:
        pbar = None

    # Query the database to get the network information.
    pybrain_network = pgdb.getNetworkByID(args.network)

    temp_f_h, temp_f_network = tempfile.mkstemp()
    os.close(temp_f_h)

    with open(temp_f_network, "w") as f:
        pickle.dump(pybrain_network, f)

    # TODO: Need to fix this for chemistry support here.
    if "Chemical" in pybrain_network.name:
        chem_re = re.compile(
                "JL NN Chemical DL([0-9]+) \([0-9]+,[0-9]+,[0-9]+\) v[0-9]+")
        chem_dl_length = int(chem_re.findall(pybrain_network.name)[0])

        network_params_len = len(pybrain_network.params) + chem_dl_length * 3

    else:
        network_params_len = len(pybrain_network.params)

    for curr_repeat in range(0, args.repeat):
        repeat_start_time = datetime.datetime.now()

        gens_stat_list = []

        # Prepare the array for storing hall of fame.
        hof_array = np.zeros((args.generations,
            network_params_len))

        if(args.enable_zmq_updates):
            # Configure ZMQ - Publisher role
            context   = zmq.Context()
            sender    = context.socket(zmq.PUSH)
            sender.bind("tcp://*:9854")

        toolbox = base.Toolbox()
        toolbox.register("map", scoop.futures.map)
        toolbox.register("attr_float", random.uniform,
            a=args.weight_min, b=args.weight_max)
        toolbox.register("individual", tools.initRepeat, creator.Individual,
            toolbox.attr_float, n=network_params_len)
        toolbox.register("population", tools.initRepeat, list,
            toolbox.individual)

        # Query the database to get the trail information.
        (data_matrix,
        db_trail_name,
        init_rot) = pgdb.getTrailData(args.trail)

        toolbox.register("evaluate", __singleMazeTask, moves=args.moves,
            trail_matrix=data_matrix, trail_name=db_trail_name,
            trail_rot=init_rot, pb_filename=temp_f_network)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutFlipBit, indpb=P_BIT_MUTATE)
        toolbox.register("select", tools.selTournament,
            tournsize=args.elite_count)

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
                cxpb=args.prob_crossover, mutpb=args.prob_mutate)

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

            # Record the statistics for this run.
            elite_food, elite_moves, this_move_stats = (
            __singleMazeTask(
                individual=tools.selBest(population, k=1)[0],
                moves=args.moves,
                trail_matrix=data_matrix,
                trail_name=temp_f_network,
                trail_rot=init_rot,
                pb_filename=temp_f_network,
                detailed_stats=True))

            logging.debug("Elite Gen {0} - Food: {1} Moves: {2}".format(
                gen,
                elite_food,
                elite_moves))

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
            run_info["elite_count"]  = args.elite_count
            run_info["p_mutate"]     = args.prob_mutate
            run_info["p_crossover"]  = args.prob_crossover
            run_info["weight_min"]   = args.weight_min
            run_info["weight_max"]   = args.weight_max
            run_info["debug"]        = args.debug
            run_info["runtime"]      = (datetime.datetime.now() -
                repeat_start_time)

            pgdb.recordRun(run_info, gens_stat_list)

    # Calculate and display the total runtime
    if pbar:
        pbar.finish()
    total_time_s = time.time() - run_date

    # Delete the temporary file
    os.remove(temp_f_network)

    logging.info("Run T{0} G{1} P{2} N{3} M{4} completed in {5}".format(
        args.trail,
        args.generations,
        args.population,
        args.network,
        args.moves,
        time.strftime('%H:%M:%S', time.gmtime(total_time_s))))


if __name__ == "__main__":
    main()






