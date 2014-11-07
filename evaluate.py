"""Script to evaluate a trail with given run.

Example:
  Users simply need to specify a run id and script will return a URL
  that points to an animation for the given trail.

      $ python evaluate.py 15

"""
import argparse
import json
import urllib
import urllib2

from GATools.DBUtils import DBUtils
from GATools.trail.network import network as network
from GATools.trail.trail import trail as trail

P_BIT_MUTATE    = 0.05
CONFIG_FILE = "config/config.json"
BASE_URL = "{0}/animate/{1}/{2}"

def eval_trail(individual, moves, network_id, trail_id):
    an = network()
    at = trail()

    # Read in the network.
    an.read_network_by_id(network_id, CONFIG_FILE)

    at.readTrail(trail_id, CONFIG_FILE)

    an.updateParameters(individual)

    moves_list = []

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

        moves_list.append(currMove)

    return moves_list

def shorten_url(url, api_key, debug=False):
    """ Takes a URL and shortens it with Google shortener API. """

    data = { "longUrl" : url }

    api_url = ("https://www.googleapis.com/urlshortener/"
        "v1/url?key={0}".format(api_key))

    if debug:
        print "JSON data is {0}".format(data)
        print "Submitting to URL {0}".format(api_url)

    req = urllib2.Request(api_url)
    req.add_header('Content-Type', 'application/json')
    resp = urllib2.urlopen(req, json.dumps(data))

    ret_data = json.loads(resp.read())

    if debug:
        print ret_data

    return ret_data["id"]

def main():
    parser = argparse.ArgumentParser(
        description='Proces trail on an elite.')
    parser.add_argument('run_id', type=int,
        help='The run ID to fetch animations for.')
    parser.add_argument('-g', '--generation', type=int,
        default=None,
        help='The generation to evaluate elite for.')
    parser.add_argument('--no-shorten', action='store_true',
        help='Disables URL shortening with Google.')
    parser.add_argument('--debug', action='store_true',
        help='Enables debug information.')

    args = parser.parse_args()

    # Read the configuration file.
    with open(CONFIG_FILE) as fh:
        config = json.load(fh)

    pgdb = DBUtils(CONFIG_FILE)

    elite = pgdb.get_elite(args.run_id, args.generation)

    run_info = pgdb.get_run_info(args.run_id)

    moves = eval_trail(elite, run_info["moves_limit"],
        run_info["networks_id"], run_info["trails_id"])

    actual_url = BASE_URL.format(
        config["base-viewer-url"],
        run_info["trails_id"],
        "".join([str(x) for x in moves]))

    if args.debug:
        print "DEBUG: Base URL is {0}.".format(actual_url)

    if not args.no_shorten:
        print_url = shorten_url(actual_url, config["url-shorten-key"],
            args.debug)
    else:
        print_url = actual_url

    print "Animation URL: {0}".format(print_url)

if __name__ == "__main__":
    main()
