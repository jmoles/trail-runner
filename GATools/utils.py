import argparse
import logging
import textwrap
import sys

# Local imports
from DBUtils import DBUtils

GENS_DEF        = 200
P_MUTATE_DEF    = 0.1
P_CROSSOVER_DEF = 0.5
WEIGHT_MIN_DEF  = -5.0
WEIGHT_MAX_DEF  = 5.0
SELECTION_DEF   = 3
MUTATE_DEF      = 1
VARIATION_DEF   = 2

DEF_ERROR_VAL = None

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

        parser.add_argument("trail", type=int,
            metavar='trail',
            help="Trail to use.",
            choices=valid_db_opts["trail"])
        parser.add_argument("population", type=int,
            metavar=u"\u03BC",
            help="Size of the population. Serves as "
                u"\u03BC" " in varOr type runs.")
        parser.add_argument("lambda_",
            metavar=u"\u03BB",
            type=int,
            help="Size of the offspring pool (" u"\u03BB" "). "
                "Required in varOr type runs.")
        parser.add_argument("moves",
            type=int,
            metavar="moves",
            help="Maximum moves for agent.")
        parser.add_argument("network", type=int,
            metavar='network',
            nargs='*',
            help=textwrap.dedent("Network type to use."),
            choices=valid_db_opts["network"])

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
        group.add_argument("--variation", type=int,
            default=VARIATION_DEF,
            help="Variation type to use in DEAP.",
            choices=valid_db_opts["variations"])
        group.add_argument("--mutate-type", type=int, nargs="?",
            default=MUTATE_DEF,
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

        group = parser.add_argument_group('Genetic Algorithm '
            'Selection Configuration')
        group.add_argument("-s", "--selection", type=int,
            default=SELECTION_DEF,
            help="Selection type to use.",
            choices=valid_db_opts["selection"])
        group.add_argument("--tournament-size", type=int,
            default=DEF_ERROR_VAL,
            help="If using tournament selection, the size of the tournament.")

        args = parser.parse_args()

        utils.__check_args(args)

        return args

    @staticmethod
    def __check_args(args):
        if args.weight_min > args.weight_max:
            logging.critical("Minimum weight must be greater than max weight.")
            sys.exit(1)

        if args.selection == 1 and args.tournament_size == DEF_ERROR_VAL:
            # Tournament selected checking.
            logging.critical("Tournament size (--tournament-size) "
                "must be specified when using tournament selection type!");
            sys.exit(1)
        elif (args.selection == 3 or args.selection == 4):
            # NSGA2 or SPEA2 selected checking.
            if args.variation != 2:
                logging.critical("Variation must be set to varOr (2) for "
                "NSGA2 or SPEA2 selection type!")
                sys.exit(1)

        if args.variation == 2 and args.lambda_ == DEF_ERROR_VAL:
            logging.critical(u"\u03BB" " must be specified for variation "
            "varOr.")
            sys.exit(1)

        if (args.lambda_ is not DEF_ERROR_VAL
            and args.lambda_ <= args.population):
            logging.critical(u"\u03BB" " must be greater than population ("
            u"\u03BC" ")!")
            sys.exit(1)
