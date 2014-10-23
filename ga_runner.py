import datetime
from deap import algorithms, base, creator, tools
import logging
import numpy as np
import os
try:
   import cPickle as pickle
except:
   import pickle
import random
import re
from scipy.stats import mode
import scoop
import socket
import sys
import tempfile

import time

from GATools.trail.network import network as AgentNetwork
from GATools.trail.trail import trail as AgentTrail
from GATools.DBUtils import DBUtils

from GATools.utils import utils

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
# This is tied to values in database.
SELECTION_MODES = [
    None,
    tools.selTournament,
    tools.selRoulette,
    tools.selNSGA2,
    tools.selSPEA2,
    tools.selRandom,
    tools.selBest,
    tools.selWorst,
    tools.selTournamentDCD,
]

def __singleMazeTask(individual, moves, network, trail,
    gen=None, record=None):

    start_time = datetime.datetime.now()

    an = pickle.loads(network)
    at = pickle.loads(trail)

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

    if gen is None:
        return (at.getFoodConsumed(), at.getNumMoves())
    else:
        this_move_stats = at.getMovesStats()

        record_info                  = {}
        record_info["gen"]           = gen - 1
        record_info["runtime"]       = (datetime.datetime.now() -
                start_time)
        record_info["food_max"]      = record["food"]["max"]
        record_info["food_min"]      = record["food"]["min"]
        record_info["food_avg"]      = record["food"]["avg"]
        record_info["food_std"]      = record["food"]["std"]
        record_info["food_mode"]     = record["food"]["mode"]
        record_info["moves_max"]     = record["moves"]["max"]
        record_info["moves_min"]     = record["moves"]["min"]
        record_info["moves_avg"]     = record["moves"]["avg"]
        record_info["moves_std"]     = record["moves"]["std"]
        record_info["moves_mode"]    = record["moves"]["mode"]
        record_info["moves_left"]    = this_move_stats["left"]
        record_info["moves_right"]   = this_move_stats["right"]
        record_info["moves_forward"] = this_move_stats["forward"]
        record_info["moves_none"]    = this_move_stats["none"]
        record_info["elite"]         = np.array(individual).tolist()

        return (gen, record_info)

def main(args):
    run_date = time.time()

    # Configure Logging
    root = logging.getLogger()
    if(args.debug):
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)

    if args.quiet:
        root.propogate = False

    # Set up the database.
    pgdb = DBUtils()

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

        gens_stat_list = [0] * args.generations
        # Create an empty array to store the launches for SCOOP.
        launches = []

        # Prepare the array for storing hall of fame.
        hof_array = np.zeros((args.generations,
            network_params_len))

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

        an_temp = AgentNetwork()
        an_temp.readNetworkFromFile(temp_f_network)
        at_temp = AgentTrail()
        at_temp.readTrailInstant(data_matrix, db_trail_name, init_rot)

        toolbox.register("evaluate", __singleMazeTask, moves=args.moves,
            network=pickle.dumps(an_temp), trail=pickle.dumps(at_temp))
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutFlipBit, indpb=P_BIT_MUTATE)
        if args.selection == 1:
            # Selection is tournment. Must use argument from user.
            toolbox.register("select", tools.selTournament,
                tournsize=args.tournament_size)
        else:
            # Selection is something else.
            # Indexes start with 1 in Postgres so need to offset by 1 here.
            toolbox.register("select", SELECTION_MODES[args.selection])

        # Start a new evolution
        population = toolbox.population(n=args.population)
        halloffame = tools.HallOfFame(maxsize=1)
        food_stats = tools.Statistics(key=lambda ind: ind.fitness.values[0])
        move_stats = tools.Statistics(key=lambda ind: ind.fitness.values[1])
        mstats     = tools.MultiStatistics(food=food_stats, moves=move_stats)

        mstats.register("min", np.min)
        mstats.register("avg", np.mean)
        mstats.register("max", np.max)
        mstats.register("std", np.std)
        mstats.register("mode", mode)

        # Record the start of this run.
        log_time = datetime.datetime.now()

        # Begin the generational process
        for gen in range(1, args.generations + 1):

            gen_start_time = datetime.datetime.now()

            # Select the next generation individuals and vary
            # unless they are the first generation.
            if gen == 1:
                offspring = population
            else:
                offspring = toolbox.select(population, k=len(population))

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

            logging.debug("Completed generation {0}".format(gen))

            hof_indiv = np.array(tools.selBest(population, k=1)[0])

            hof_array[gen - 1] = hof_indiv

            # Add the hall of fame to launches.
            launches.append(
                scoop.futures.submit(__singleMazeTask,
                hof_indiv,
                args.moves,
                pickle.dumps(an_temp),
                pickle.dumps(at_temp),
                gen,
                record)
            )

            # Update the progress bar
            if pbar:
                bar_done_val = ((float(percent_done) / (100.0 * args.repeat)) +
                    (float(curr_repeat)) / (float(args.repeat)))
                pbar.update(bar_done_val * 100)

        # Evaluate the Hall of Fame individual for each generation here
        # in a multithreaded fashion to speed things up.
        for this_future in scoop.futures.as_completed(launches):
            result = this_future.result()
            gens_stat_list[result[0] - 1] = result[1]

        # Record the statistics on this run.
        run_info = {}

        run_info["trails_id"]    = args.trail
        run_info["networks_id"]  = args.network
        run_info["selection_id"] = args.selection
        run_info["mutate_id"]    = args.mutate_type
        run_info["host_type_id"] = 1 # Only one host type for now.
        run_info["run_date"]     = log_time
        run_info["hostname"]     = socket.getfqdn()
        run_info["generations"]  = args.generations
        run_info["population"]   = args.population
        run_info["moves_limit"]  = args.moves
        if args.selection == 1:
            run_info["sel_tourn_size"]  = args.tournament_size
        run_info["p_mutate"]     = args.prob_mutate
        run_info["p_crossover"]  = args.prob_crossover
        run_info["weight_min"]   = args.weight_min
        run_info["weight_max"]   = args.weight_max
        run_info["debug"]        = args.debug
        run_info["runtime"]      = (datetime.datetime.now() -
            repeat_start_time)

        if not args.disable_db:
            run_id = pgdb.recordRun(run_info, gens_stat_list)
        else:
            run_id = -1

    # Calculate and display the total runtime
    if pbar:
        pbar.finish()
    total_time_s = time.time() - run_date

    # Delete the temporary file
    os.remove(temp_f_network)

    if run_id > 0:
        logging.info("Run ID {0} T{1} G{2} P{3}"
            " N{4} M{5} completed in {6}".format(
                run_id,
                args.trail,
                args.generations,
                args.population,
                args.network,
                args.moves,
                time.strftime('%H:%M:%S', time.gmtime(total_time_s))))
    else:
        logging.info("UNLOGGED Run T{0} G{1} P{2}"
            " N{3} M{4} completed in {5}".format(
                args.trail,
                args.generations,
                args.population,
                args.network,
                args.moves,
                time.strftime('%H:%M:%S', time.gmtime(total_time_s))))

if __name__ == "__main__":
    args = utils.parse_args()
    main(args)
