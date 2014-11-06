from collections import Sequence
import datetime
from deap import algorithms, base, creator, tools
from itertools import repeat
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
    print ("WARNING: progressbar2 library is not available. " +
        "Try 'pip install progressbar2'")

# Configure DEAP
creator.create("FitnessMulti", base.Fitness, weights=(1.0,-0.1))
creator.create("Individual", list, fitness=creator.FitnessMulti)

# Some constants
P_BIT_MUTATE    = 0.05
DB_CONFIG_FILE = "config/config.json"

def mutUniformFloat(individual, low, up, indpb):
    """Mutate an individual by replacing attributes, with probability *indpb*,
    by a integer uniformly drawn between *low* and *up* inclusively.

    :param individual: :term:`Sequence <sequence>` individual to be mutated.
    :param low: The lower bound or a :term:`python:sequence` of
                of lower bounds of the range from wich to draw the new
                integer.
    :param up: The upper bound or a :term:`python:sequence` of
               of upper bounds of the range from wich to draw the new
               integer.
    :param indpb: Independent probability for each attribute to be mutated.
    :returns: A tuple of one individual.
    """
    size = len(individual)
    if not isinstance(low, Sequence):
        low = repeat(low, size)
    elif len(low) < size:
        raise IndexError("low must be at least the size of individual: %d < %d" % (len(low), size))
    if not isinstance(up, Sequence):
        up = repeat(up, size)
    elif len(up) < size:
        raise IndexError("up must be at least the size of individual: %d < %d" % (len(up), size))

    for i, xl, xu in zip(xrange(size), low, up):
        if random.random() < indpb:
            individual[i] = random.uniform(xl, xu)

    return individual,

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
    pgdb = DBUtils(config_file=DB_CONFIG_FILE)

    # Get the name of this agent trail for later use
    at = AgentTrail()
    at.readTrail(args.trail, DB_CONFIG_FILE)
    trail_name = at.getName()

    if not args.quiet and not args.debug and not args.script_mode:
        try:
            TOTAL_GENERATIONS = (len(args.network) *
                args.generations * args.repeat)
            widgets = ['Processed: ', progressbar.Percentage(), ' ',
                progressbar.Bar(marker=progressbar.RotatingMarker()),
                ' ', progressbar.ETA()]
            pbar = progressbar.ProgressBar(
                widgets=widgets,
                maxval=TOTAL_GENERATIONS).start()
        except:
            pbar = None
    else:
        pbar = None

    current_overall_gen = 0

    for curr_network in args.network:

        # Query the database to get the network information.
        pybrain_network = pgdb.getNetworkByID(curr_network)

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

        # Query the database to get the trail information.
        (data_matrix,
        db_trail_name,
        init_rot) = pgdb.getTrailData(args.trail)

        # Calculate the maximum amount of food for potential later comparison.
        MAX_FOOD = np.bincount(np.array(data_matrix).flatten())[1]

        for curr_repeat in range(0, args.repeat):
            repeat_start_time = datetime.datetime.now()

            gens_stat_list = [None] * args.generations
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

            an_temp = AgentNetwork()
            an_temp.readNetworkFromFile(temp_f_network)
            at_temp = AgentTrail()
            at_temp.readTrailInstant(data_matrix, db_trail_name, init_rot)

            toolbox.register("evaluate", __singleMazeTask, moves=args.moves,
                network=pickle.dumps(an_temp), trail=pickle.dumps(at_temp))
            toolbox.register("mate", tools.cxTwoPoint)
            if args.mutate_type == 1:
                toolbox.register("mutate",
                    tools.mutFlipBit,
                    indpb=P_BIT_MUTATE)
            elif args.mutate_type == 2:
                toolbox.register("mutate",
                    mutUniformFloat,
                    low=args.weight_min,
                    up=args.weight_max,
                    indpb=P_BIT_MUTATE)
            elif args.mutate_type == 3:
                toolbox.register("mutate",
                    mutUniformFloat,
                    low=args.weight_min,
                    up=args.weight_max,
                    indpb=0.30)
            elif args.mutate_type == 4:
                toolbox.register("mutate",
                    mutUniformFloat,
                    low=args.weight_min,
                    up=args.weight_max,
                    indpb=0.10)
            elif args.mutate_type == 5:
                toolbox.register("mutate",
                    tools.mutGaussian,
                    mu=0,
                    indpb=0.05)
            else:
                print "ERROR: Please selct a valid mutate type!"
                sys.exit(10)

            if args.selection == 1:
                # Selection is tournment. Must use argument from user.
                toolbox.register("select", tools.selTournament,
                    tournsize=args.tournament_size)
            elif args.selection == 2:
                toolbox.register("select", tools.selRoulette)
            elif args.selection == 3:
                toolbox.register("select", tools.selNSGA2)
            elif args.selection == 4:
                toolbox.register("select", tools.selSPEA2)
            elif args.selection == 5:
                toolbox.register("select", tools.selRandom)
            elif args.selection == 6:
                toolbox.register("select", tools.selBest)
            elif args.selection == 7:
                toolbox.register("select", tools.selWorst)
            elif args.selection == 8:
                toolbox.register("select", tools.selTournamentDCD)
            else:
                print "ERROR: Something is wrong with selection method!"
                sys.exit(10)

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

            # Evaluate and record the first generation here.
            invalid_ind = [ind for ind in population if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # Determine the current generations statistics.
            record = mstats.compile(population)

            if args.debug:
                print "DEBUG: Completed generation 1"

            hof_indiv = np.array(tools.selBest(population, k=1)[0])
            hof_array[0] = hof_indiv

            # Add the hall of fame to launches.
            launches.append(
                scoop.futures.submit(__singleMazeTask,
                hof_indiv,
                args.moves,
                pickle.dumps(an_temp),
                pickle.dumps(at_temp),
                1,
                record)
            )

            # Keep track of the average food history.
            mean_food_history = []
            smart_term_msg = ""

            # Begin the generational process
            for gen in range(2, args.generations + 1):
                # Vary the pool of individuals
                if args.variation in [1]:
                    offspring = algorithms.varAnd(population, toolbox,
                        cxpb=args.prob_crossover, mutpb=args.prob_mutate)
                elif args.variation in [2, 3, 4]:
                    offspring = algorithms.varOr(population, toolbox,
                        lambda_=args.lambda_,
                        cxpb=args.prob_crossover, mutpb=args.prob_mutate)
                elif args.variation in [5]:
                    # Take and modify the varAnd from DEAP.
                    offspring = [toolbox.clone(ind) for ind in population]

                    # Apply crossover and mutation on the offspring
                    for i in range(1, len(offspring), 2):
                        if random.random() < args.prob_crossover:
                            offspring[i-1], offspring[i] = toolbox.mate(
                                offspring[i-1], offspring[i])
                            del (offspring[i-1].fitness.values,
                                offspring[i].fitness.values)

                    for i in range(len(offspring)):
                        if random.random() < args.prob_mutate:
                            if args.mutate_type in [5]:
                                offspring[i], = toolbox.mutate(
                                    offspring[i],
                                    sigma=np.std(offspring[i]))
                            else:
                                offspring[i], = toolbox.mutate(
                                    offspring[i], offspring[i])
                            del offspring[i].fitness.values

                else:
                    print ("ERROR: Something is really wrong! " +
                        "Reached an invalid variation type!")
                    sys.exit(5)

                # Evaluate the individuals with an invalid fitness
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit

                # Update the hall of fame with the generated individuals
                if halloffame is not None:
                    halloffame.update(offspring)

                # Replace the current population by the offspring
                if args.variation in [2, 3]:
                    population[:] = toolbox.select(offspring, args.population)
                elif args.variation in [4, 5]:
                    population[:] = toolbox.select(offspring + population,
                        args.population)
                else:
                    population[:] = offspring

                # Determine the current generations statistics.
                record = mstats.compile(population)

                if args.debug:
                    print "DEBUG: Completed generation {0}.".format(gen)
                    print (
                        "DEBUG: Food (Min / Max / Avg / Std / Mode): "
                              "{0} / {1} / {2} / {3} / {4}".format(
                                record["food"]["min"],
                                record["food"]["max"],
                                record["food"]["avg"],
                                record["food"]["std"],
                                record["food"]["mode"]))
                    print (
                        "DEBUG: Moves (Min / Max / Avg / Std / Mode): "
                              "{0} / {1} / {2} / {3} / {4}".format(
                                record["moves"]["min"],
                                record["moves"]["max"],
                                record["moves"]["avg"],
                                record["moves"]["std"],
                                record["moves"]["mode"]))

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

                # Update the mean food history.
                mean_food_history.append(record["food"]["avg"])

                # Update the progress bar
                if pbar:
                    current_overall_gen += 1
                    pbar.update(current_overall_gen)

                # Check if it is time to quit if variation is 3. Critera are
                # any of the following:
                #  1) All food has been collected.
                #  2) Mean has not changed for args.mean_check_length
                #  3) Run out of generations (happens without this if)
                if args.variation in [3, 4, 5] and not args.no_early_quit:
                    if (record["food"]["max"] == MAX_FOOD):
                        smart_term_msg = ("Exited at generation {0} because "
                            "all food was consumed.").format(gen)
                    elif(len(mean_food_history) >= args.mean_check_length and
                        (np.std(mean_food_history[-args.mean_check_length:])
                            < 0.1)):
                        smart_term_msg = ("Exited at generation {0} because "
                            "mean check length has been met.").format(gen)
                        break


            # Evaluate the Hall of Fame individual for each generation here
            # in a multithreaded fashion to speed things up.
            for this_future in scoop.futures.as_completed(launches):
                result = this_future.result()
                gens_stat_list[result[0] - 1] = result[1]

            # Remove all of the None values from the gen_stat_list
            gens_stat_list = filter(lambda a: a is not None, gens_stat_list)

            # Record the statistics on this run.
            run_info = {}

            run_info["trails_id"]    = args.trail
            run_info["networks_id"]  = curr_network
            run_info["selection_id"] = args.selection
            run_info["mutate_id"]    = args.mutate_type
            run_info["host_type_id"] = 1 # Only one host type for now.
            run_info["variations_id"] = args.variation
            run_info["run_date"]     = log_time
            run_info["hostname"]     = socket.getfqdn()
            run_info["generations"]  = args.generations
            run_info["population"]   = args.population
            run_info["moves_limit"]  = args.moves
            run_info["sel_tourn_size"]  = args.tournament_size
            if args.variation in [1, 5]:
                run_info["lambda"] = 0
            else:
                run_info["lambda"] = args.lambda_
            run_info["p_mutate"]     = args.prob_mutate
            run_info["p_crossover"]  = args.prob_crossover
            run_info["weight_min"]   = args.weight_min
            run_info["weight_max"]   = args.weight_max
            run_info["debug"]        = args.debug
            # Version for if anything changes in python GA Algorithm
            run_info["algorithm_ver"] = 2
            run_info["mean_check_length"] = args.mean_check_length
            run_info["runtime"]      = (datetime.datetime.now() -
                repeat_start_time)

            if not args.disable_db:
                run_id = pgdb.recordRun(run_info, gens_stat_list)
            else:
                run_id = -1

            if args.script_mode:
                if run_id > 0:
                    print (
                        "Completed repeat {0} with run ID {1}. {2}".format(
                            curr_repeat,
                            run_id,
                            smart_term_msg
                        ))
                else:
                    print (
                        "Completed repeat {0} without logging to DB. {1}".format(
                            curr_repeat,
                            smart_term_msg
                        ))

        # Delete the temporary file
        os.remove(temp_f_network)

    # Calculate and display the total runtime
    if pbar:
        pbar.finish()

    total_time_s = time.time() - run_date

    if run_id > 0:
        print "Final Run ID {0} completed all runs in {1}. {2}".format(
                run_id,
                time.strftime('%H:%M:%S', time.gmtime(total_time_s)),
                smart_term_msg)
    else:
        print "UNLOGGED Run completed in {0}. {1}".format(
                time.strftime('%H:%M:%S', time.gmtime(total_time_s)),
                smart_term_msg)


if __name__ == "__main__":
    args = utils.parse_args(DB_CONFIG_FILE)
    main(args)
