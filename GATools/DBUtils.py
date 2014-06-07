import numpy as np
import os
import psycopg2

try:
    import cPickle as pickle
except:
    import pickle

try:
    import cStringIO as StringIO
except:
    import StringIO

class NetworkNotFound(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class DBUtils:
    def __init__(
        self,
        host=os.environ["PSYCOPG2_DB_HOST"],
        db=os.environ["PSYCOPG2_DB_DB"],
        user=os.environ["PSYCOPG2_DB_USER"],
        password=os.environ["PSYCOPG2_DB_PASS"]):

        self.__dsn = "host={0} dbname={1} user={2} password={3}".format(
            host, db, user, password)

        self.__conn        = None
        self.__cursor      = None

    def fetchNetworksList(self):
        net_s = ""
        net_i = []
        net_l = []

        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("SELECT id, name FROM networks")
        for idx, name in curs.fetchall():
            net_s += ("\t" + str(idx) + ": " + name + "\n")
            net_i.append(idx)
            net_l.append(name)

        curs.close()
        conn.close()

        return net_s, net_i, net_l

    def fetchNetworkCmdPrettyPrint(self):
        net_s, net_i, net_l = self.fetchNetworksList()

        return net_s, net_i

    def fetchTrailList(self):
        trail_s = ""
        trail_i = []

        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("SELECT id, name, moves FROM trails")

        for idx, name, moves in curs.fetchall():
            trail_s += ("\t" + str(idx) + ":" + name +
                " (" + str(moves) + ")\n")
            trail_i.append(idx)

        curs.close()
        conn.close()

        return trail_s, trail_i

    def getNetworks(self):
        return self.__genericDictGet("SELECT id, name FROM networks")

    def getTrails(self):
        return self.__genericDictGet("SELECT id, name FROM trails")

    def recordRun(self, run_info, gen_info):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("""
            INSERT INTO run (id, trails_id, networks_id, mutate_id,
                host_configs_id, run_date, runtime,
                hostname, generations, population,
                moves_limit, elite_count, p_mutate,
                p_crossover, weight_min, weight_max, debug)
            VALUES (
            DEFAULT,
            %(trails_id)s,
            %(networks_id)s,
            %(mutate_id)s,
            %(host_type_id)s,
            %(run_date)s,
            %(runtime)s,
            %(hostname)s,
            %(generations)s,
            %(population)s,
            %(moves_limit)s,
            %(elite_count)s,
            %(p_mutate)s,
            %(p_crossover)s,
            %(weight_min)s,
            %(weight_max)s,
            %(debug)s) RETURNING id;""", run_info)

        run_id = curs.fetchone()[0]

        for curr_gen in gen_info:
            curr_gen["run_id"] = run_id

        curs.executemany("""
            INSERT INTO generations (id, run_id, generation, runtime,
                food_max, food_min, food_avg, food_std,
                moves_max, moves_min, moves_avg, moves_std,
                moves_left, moves_right, moves_forward, moves_none,
                elite)
            VALUES (
            DEFAULT,
            %(run_id)s,
            %(gen)s,
            %(runtime)s,
            %(food_max)s,
            %(food_min)s,
            %(food_avg)s,
            %(food_std)s,
            %(moves_max)s,
            %(moves_min)s,
            %(moves_avg)s,
            %(moves_std)s,
            %(moves_left)s,
            %(moves_right)s,
            %(moves_forward)s,
            %(moves_none)s,
            %(elite)s); """, gen_info)

        conn.commit()

        curs.close()
        conn.close()


    def __genericDictGet(self, query):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        ret_dict = {}

        curs.execute(query)
        for idx, name in curs.fetchall():
            ret_dict[idx] = name

        curs.close()
        conn.close()

        return ret_dict


    def getTrailData(self, trailID):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("""SELECT trail_data, name, init_rot FROM trails
            WHERE id=%s;""", (trailID, ))

        curs_results = curs.fetchall()[0]

        curs.close()
        conn.close()

        return np.matrix(curs_results[0]), curs_results[1], curs_results[2]

    def findRuns(self, network=1, trail=3, gen=200, pop=300):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("""SELECT id
            FROM run
            WHERE trails_id=%s AND
            networks_id=%s AND
            generations=%s AND
            population=%s;""",
            (trail,
            network,
            gen,
            pop))

        ret_val = []
        for record in curs:
            ret_val.append(record[0])

        curs.close()
        conn.close()

        return ret_val

    def fetchRunGenerations(self, run_id):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        # TODO: Need to make a view to properly handle this function.

        curs.execute("""SELECT run_id, generation, runtime,
            food_min, food_max, food_avg, food_std,
            moves_min, moves_max, moves_avg, moves_std,
            moves_left, moves_right, moves_forward, moves_none
            FROM generations
            WHERE run_id IN %s;""", (tuple(run_id), ) )

        ret_val  = {}
        gen_dict = {}

        for record in curs:

            curr_run_id        = record[0]
            curr_gen           = record[1]

            food_d             = {}
            food_d["min"]      = record[3]
            food_d["max"]      = record[4]
            food_d["avg"]      = record[5]
            food_d["std"]      = record[6]

            move_d             = {}
            move_d["min"]      = record[7]
            move_d["max"]      = record[8]
            move_d["avg"]      = record[9]
            move_d["std"]      = record[10]
            move_d["left"]     = record[11]
            move_d["right"]    = record[12]
            move_d["forward"]  = record[13]
            move_d["none"]     = record[14]

            # TODO: Need to double index this table here. Once for run,
            # and then once for each generation.
            curr_dict          = { "food" : food_d, "moves" : move_d }

            if curr_run_id in ret_val:
                ret_val[curr_run_id][curr_gen] = curr_dict
            else:
                init_dict = {curr_gen : curr_dict }
                ret_val[curr_run_id] = init_dict

        curs.close()
        conn.close()

        return ret_val

    def fetchRunInfo(self, run_id):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("""SELECT id, trails_id, networks_id, mutate_id,
            host_configs_id, run_date, runtime, hostname, generations,
            population, moves_limit, elite_count, p_mutate, p_crossover,
            weight_min, weight_max, debug
            FROM run
            WHERE id IN %s;""", (tuple(run_id), ) )

        ret_val = {}

        for record in curs:
            curr_dict                    = {}

            this_run_id                  = record[0]
            curr_dict["trails_id"]       = record[1]
            curr_dict["networks_id"]     = record[2]
            curr_dict["mutate_id"]       = record[3]
            curr_dict["host_configs_id"] = record[4]
            curr_dict["run_date"]        = record[5]
            curr_dict["runtime"]         = record[6]
            curr_dict["hostname"]        = record[7]
            curr_dict["generations"]     = record[8]
            curr_dict["population"]      = record[9]
            curr_dict["moves_limit"]     = record[10]
            curr_dict["elite_count"]     = record[11]
            curr_dict["p_mutate"]        = record[12]
            curr_dict["p_crossover"]     = record[13]
            curr_dict["weight_min"]      = record[14]
            curr_dict["weight_max"]      = record[15]
            curr_dict["debug"]           = record[16]

            ret_val[this_run_id]       = curr_dict

        curs.close()
        conn.close()

        return ret_val

    def getSameRunIDs(self, run_id):
        """ Takes a single run_id and returns a list of run_ids that
        were run with the same parameters.

        Returns:
           list. A list of run_id (as int) that have same parameters as
               the passed in run_id.

        """
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        # First, fetch the parameters that this run went with.
        this_run_d = self.fetchRunInfo([run_id])[run_id]

        # Now, excute a query that has that matches this run info.
        curs.execute("""SELECT id
            FROM run
            WHERE trails_id = %s AND
            networks_id = %s AND
            mutate_id = %s AND
            generations = %s AND
            population = %s AND
            moves_limit = %s AND
            elite_count = %s AND
            round(p_mutate::numeric, 4) = %s AND
            round(p_crossover::numeric, 4) = %s AND
            weight_min = %s AND
            weight_max = %s AND
            debug = %s;""", (
            this_run_d["trails_id"],
            this_run_d["networks_id"],
            this_run_d["mutate_id"],
            this_run_d["generations"],
            this_run_d["population"],
            this_run_d["moves_limit"],
            this_run_d["elite_count"],
            round(this_run_d["p_mutate"], 4),
            round(this_run_d["p_crossover"], 4),
            this_run_d["weight_min"],
            this_run_d["weight_max"],
            this_run_d["debug"]) )

        ret_val = []

        for record in curs:
            ret_val.append(record[0])

        curs.close()
        conn.close()

        return ret_val

    def getMaxFoodAtGeneration(self, run_ids, generation):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("""SELECT MAX(food_max) AS food_max
            FROM generations
            WHERE generation=%s AND
            run_id IN %s;""", (generation - 1, tuple(run_ids), ) )

        ret_val = curs.fetchall()[0][0]

        curs.close()
        conn.close()

        return ret_val


    def getNetworkByID(self, network_id):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("""SELECT net
            FROM networks
            WHERE id=%s;""", (network_id, ) )

        results = curs.fetchall()

        if not results:
            print "No network was found for network_id {0}".format(network_id)
            raise NetworkNotFound(network_id)


        ret_sio = StringIO.StringIO(results[0][0])

        ret_net = pickle.load(ret_sio)

        curs.close()
        conn.close()

        return ret_net


    def getAllGenStatAverageRunIds(self, run_ids, group="food",
        stat="max", max_gen=199):
        """ Provided a tuple of run_ids, returns the average across
        all geenrations for the requested stat in the given group.

        Returns:
            list. Sorted by generation with average at each generation.
        """

        # TODO: Make this actually work.
        return

        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        if group != "food" and group != "moves":
            print "ERROR: Invalid type ({0}) of group requested!".format(group)
            return

        if (stat != "max" and stat != "min" and stat != "avg" and
            stat != "left" and stat != "right" and stat != "forward" and
            stat !="none"):
            print "ERROR: Invalid type ({0}) of stat requested!".format(stat)
            return


        sel_str = "{0}_{1}".format(group, stat)

        #TODO: Finish this query
        test_query = """SELECT food_max
        FROM generations
        WHERE ID IN (SELECT AVG(food_max::numeric)
            FROM generations
            WHERE run_id IN %s AND
            generation in )
        """


        query_str = """SELECT AVG({0}::numeric)
            FROM generations
            WHERE
                generation=%s AND
                run_id IN %s;""".format(sel_str)

        curs.execute(query_str, (generation, run_ids) )

        ret_val = curs.fetchall()[0][0]

        curs.close()
        conn.close()

        return ret_val


    def getStatAverageRunIds(self, run_ids, generation=199,
        group="food", stat="max"):
        """ Provided a tuple of run_ids, returns the average requested
        stat in the given group.

        Returns:
            Decimal: With average of requested query.

        """
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        if group != "food" and group != "moves":
            print "ERROR: Invalid type ({0}) of group requested!".format(group)
            return

        if stat != "max" and stat != "min" and stat != "avg":
            print "ERROR: Invalid type ({0}) of stat requested!".format(stat)
            return

        sel_str = "{0}_max".format(group)

        if stat == "max":
            query_str = """SELECT MAX({0}::numeric)
                FROM generations
                WHERE
                    generation=%s AND
                    run_id IN %s;""".format(sel_str)
        elif stat == "min":
            query_str = """SELECT MIN({0}::numeric)
                FROM generations
                WHERE
                    generation=%s AND
                    run_id IN %s;""".format(sel_str)
        elif stat == "avg":
            query_str = """SELECT AVG({0}::numeric)
                FROM generations
                WHERE
                    generation=%s AND
                    run_id IN %s;""".format(sel_str)

        curs.execute(query_str, (generation, run_ids) )

        ret_val = curs.fetchall()[0][0]

        curs.close()
        conn.close()

        return ret_val


    def getStatAverageLikeRunId(self, run_id, generation=199,
        group="food", stat="max"):
        """ Given a run_id, returns the average of the requested stat
        in the requested group. This function merely does the lookup of the
        getSameRunIDs as a convinence and calls getStatAverageRunIds.

        """

        run_ids = tuple(self.getSameRunIDs(run_id))

        return self.getStatAverageRunIds(run_ids, generation, group, stat)


    def getFirstRunId(self, net, gen, pop, trail=3, max_moves=325):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("""SELECT id
        FROM run
        WHERE networks_id=%s AND
        generations=%s AND
        population=%s AND
        trails_id=%s AND
        moves_limit=%s
        LIMIT 1;""", (net, gen, pop, trail, max_moves))

        ret_val = curs.fetchall()[0][0]

        curs.close()
        conn.close()

        return ret_val





