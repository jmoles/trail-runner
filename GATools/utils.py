import argparse
import logging
import textwrap

# Local imports
from DBUtils import DBUtils

GENS_DEF        = 200
POP_DEF         = 300
MOVES_DEF       = 200
ELITE_COUNT_DEF = 3
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
            help=textwrap.dedent("Network type to use."),
            choices=valid_db_opts["network"])
        parser.add_argument("-t", "--trail", type=int, nargs="?",
            default=3,
            help=textwrap.dedent(
                "Trail to use."),
            choices=valid_db_opts["trail"])

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

        utils.__check_args(args)

        return args

    @staticmethod
    def __check_args(args):
        if args.weight_min > args.weight_max:
            logging.critical("Minimum weight must be greater than max weight.")
            sys.exit(1)
