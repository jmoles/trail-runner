import argparse
import logging
import textwrap
import sys

# Local imports
from DBUtils import DBUtils

GENS_DEF        = 200
POP_DEF         = 300
MOVES_DEF       = 200
TOURN_COUNT_DEF = -255
P_MUTATE_DEF    = 0.2
P_CROSSOVER_DEF = 0.5
WEIGHT_MIN_DEF  = -5.0
WEIGHT_MAX_DEF  = 5.0

class utils:

    @staticmethod
    def parse_args():
        # Query the database to gather some items for argument output.
        pgdb = DBUtils()
        valid_db_opts = pgdb.getIDs()

        # Parse the arguments
        parser = argparse.ArgumentParser(
            description="Launches SCOOP parallelized version "
            "of genetic algorithm evaluation.",
            formatter_class=argparse.RawTextHelpFormatter)

        parser.add_argument("network", type=int, nargs="?",
            metavar='network',
            help=textwrap.dedent("Network type to use."),
            choices=valid_db_opts["network"])
        parser.add_argument("trail", type=int, nargs="?",
            metavar='trail',
            help="Trail to use.",
            choices=valid_db_opts["trail"])

        group = parser.add_argument_group('Application Options')
        group.add_argument("--disable-db",
            action='store_true',
            help="Disables logging of run to database.")
        group.add_argument("--debug",
            action='store_true',
            help="Enables debug messages and flag for data in DB.")
        group.add_argument("-q", "--quiet",
            action='store_true',
            help="Disables all output from application.")
        group.add_argument("-r", "--repeat", type=int, nargs="?",
            default=1, help="Number of times to repeat simulations.")

        group = parser.add_argument_group('Genetic Algorithm Configuration')
        group.add_argument("-g", "--generations", type=int, nargs="?",
            default=GENS_DEF,
            help="Number of generations to run for.")
        group.add_argument("-p", "--population", type=int, nargs="?",
            default=POP_DEF,
            help="Size of the population.")
        group.add_argument("-m", "--moves", type=int, nargs="?",
            default=MOVES_DEF,
            help="Maximum moves for agent.")
        group.add_argument("--mutate-type", type=int, nargs="?",
            default=1,
            help="Mutation type.",
            choices=valid_db_opts["mutate"])
        group.add_argument("--prob-mutate", type=float, nargs="?",
            default=P_MUTATE_DEF,
            help="Probability of a mutation to occur.")
        group.add_argument("--prob-crossover", type=float, nargs="?",
            default=P_CROSSOVER_DEF,
            help="Probability of crossover to occur.")
        group.add_argument("--weight-min", type=float, nargs="?",
            default=WEIGHT_MIN_DEF,
            help="Minimum weight.")
        group.add_argument("--weight-max", type=float, nargs="?",
            default=WEIGHT_MAX_DEF,
            help="Maximum weight")

        group = parser.add_argument_group('Genetic Algorithm Selection Configuration')
        group.add_argument("-s", "--selection", type=int,
            default=1,
            help="Selection type to use.",
            choices=valid_db_opts["selection"])
        group.add_argument("--tournament-size", type=int,
            default=TOURN_COUNT_DEF,
            help="If using tournament selection, the size of the tournament.")

        args = parser.parse_args()

        utils.__check_args(args)

        return args

    @staticmethod
    def __check_args(args):
        if args.weight_min > args.weight_max:
            logging.critical("Minimum weight must be greater than max weight.")
            sys.exit(1)

        if args.selection == 1 and args.tournament_size == -255:
            logging.critical("Tournament size (--tournament-size) "
                "must be specified when using tournmanet selection type!");
            sys.exit(1)
