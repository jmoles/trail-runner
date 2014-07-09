from contextlib import contextmanager
import numpy as np
import os
import psycopg2
import psycopg2.pool
import sys

try:
    import cPickle as pickle
except:
    import pickle

try:
    import cStringIO as StringIO
except:
    import StringIO


class VALID_COLUMNS:
    RUN_CONFIG = (
        "id",
        "networks_id",
        "trails_id",
        "mutate_id",
        "generations",
        "population",
        "moves_limit",
        "elite_count",
        "p_mutate",
        "p_crossover",
        "weight_min",
        "weight_max",
        "RowNumber")


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
        password=os.environ["PSYCOPG2_DB_PASS"],
        debug=False):

        self.__dsn = "host={0} dbname={1} user={2} password={3}".format(
            host, db, user, password)

        self.__conn        = None
        self.__cursor      = None

        self.__debug       = debug

        self.__pool        = psycopg2.pool.SimpleConnectionPool(
            1,
            10,
            self.__dsn)

    @contextmanager
    def __getCursor(self):
        con = self.__pool.getconn()
        try:
            yield con.cursor()
        finally:
            self.__pool.putconn(con)

    def fetchNetworksList(self):
        net_s = ""
        net_i = []
        net_l = []

        with self.__getCursor() as curs:
            curs.execute("SELECT id, name FROM networks")
            for idx, name in curs.fetchall():
                net_s += ("\t" + str(idx) + ": " + name + "\n")
                net_i.append(idx)
                net_l.append(name)

        return net_s, net_i, net_l

    def fetchNetworkCmdPrettyPrint(self):
        net_s, net_i, net_l = self.fetchNetworksList()

        return net_s, net_i

    def fetchTrailList(self):
        trail_s = ""
        trail_i = []

        with self.__getCursor() as curs:
            curs.execute("SELECT id, name, moves FROM trails")

            for idx, name, moves in curs.fetchall():
                trail_s += ("\t" + str(idx) + ":" + name +
                    " (" + str(moves) + ")\n")
                trail_i.append(idx)

        return trail_s, trail_i

    def getNetworks(self):
        return self.__genericDictGet("SELECT id, name FROM networks")

    def getTrails(self):
        return self.__genericDictGet("SELECT id, name FROM trails")

    def getMutates(self):
        return self.__genericDictGet("SELECT id, name FROM mutate")

    def getRunConfigID(self, run_info):
        """ Gets the id in the run_config table based off a run_info dict.

        This is performed by checking if the configuration of the run exists
        in the database. If it does not, it is added and a run
        configuration id is created and returned.

        If debug is set, operation will not commit.
        """
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        curs.execute("""SELECT id
            FROM run_config
            WHERE
            networks_id                    = %s AND
            trails_id                      = %s AND
            mutate_id                      = %s AND
            generations                    = %s AND
            population                     = %s AND
            moves_limit                    = %s AND
            elite_count                    = %s AND
            round(p_mutate::numeric, 4)    = %s AND
            round(p_crossover::numeric, 4) = %s AND
            weight_min                     = %s AND
            weight_max                     = %s
            """, (
                run_info["networks_id"],
                run_info["trails_id"],
                run_info["mutate_id"],
                run_info["generations"],
                run_info["population"],
                run_info["moves_limit"],
                run_info["elite_count"],
                round(run_info["p_mutate"], 4),
                round(run_info["p_crossover"], 4),
                run_info["weight_min"],
                run_info["weight_max"]
        ))

        # If no row is found, need to add it and get id.
        if curs.rowcount < 1:
            if self.__debug:
                print "DEBUG: Row did not exist. Would have inserted row."

            curs.execute("""INSERT INTO run_config (
                    networks_id,
                    trails_id,
                    mutate_id,
                    generations,
                    population,
                    moves_limit,
                    elite_count,
                    p_mutate,
                    p_crossover,
                    weight_min,
                    weight_max
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;""", (
                    run_info["networks_id"],
                    run_info["trails_id"],
                    run_info["mutate_id"],
                    run_info["generations"],
                    run_info["population"],
                    run_info["moves_limit"],
                    run_info["elite_count"],
                    run_info["p_mutate"],
                    run_info["p_crossover"],
                    run_info["weight_min"],
                    run_info["weight_max"]
            ))
        elif self.__debug:
            print "DEBUG: Row was found!"

        # Get the run_id from either first search or second insert.
        run_id = curs.fetchone()[0]

        if not self.__debug:
            conn.commit()
        else:
            conn.rollback()
            print "DEBUG: id of the row was {0}.".format(run_id)

        curs.close()
        conn.close()

        return run_id

    def recordRun(self, run_info, gen_info):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        # See if this configuration exists in the run_configurations.
        # Add it to the table if not, if so, just use the config_id.
        config_id = self.getRunConfigID(run_info)

        curs.execute("""
            INSERT INTO run (id,
                host_configs_id,
                run_date,
                runtime,
                hostname,
                debug,
                run_config_id)
            VALUES (
            DEFAULT, %s, %s, %s, %s, %s, %s) RETURNING id;""", (
            run_info["host_type_id"],
            run_info["run_date"],
            run_info["runtime"],
            run_info["hostname"],
            run_info["debug"],
            config_id))

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
        ret_dict = {}

        with self.__getCursor() as curs:
            curs.execute(query)
            for idx, name in curs.fetchall():
                ret_dict[idx] = name

        return ret_dict


    def getTrailData(self, trailID):
        with self.__getCursor() as curs:
            curs.execute("""SELECT trail_data, name, init_rot FROM trails
                WHERE id=%s;""", (trailID, ))

            curs_results = curs.fetchall()[0]

        return np.matrix(curs_results[0]), curs_results[1], curs_results[2]

    def fetchRunGenerations(self, run_id):

        # TODO: Need to make a view to properly handle this function.

        with self.__getCursor() as curs:
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

        return ret_val

    def fetchRunInfo(self, run_id):
        if isinstance(run_id, int):
            run_id = (run_id, )

        with self.__getCursor() as curs:
            curs.execute("""SELECT run.id, trails_id, networks_id, mutate_id,
                host_configs_id, run_date, runtime, hostname, generations,
                population, moves_limit, elite_count, p_mutate, p_crossover,
                weight_min, weight_max, debug, run_config.id
                FROM run
                INNER JOIN run_config
                ON run.run_config_id = run_config.id
                WHERE run.id IN %s;""", (tuple(run_id), ) )

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
                curr_dict["run_config_id"]   = record[17]

                ret_val[this_run_id]       = curr_dict

        return ret_val

    def getSameRunIDs(self, run_id):
        """ Takes a single run_id and returns a list of run_ids that
        were run with the same parameters.

        Returns:
           list. A list of run_id (as int) that have same parameters as
               the passed in run_id.

        """
        with self.__getCursor() as curs:
            curs.execute("""SELECT id FROM run WHERE run_config_id =
                (SELECT run_config_id FROM run WHERE id = %s);""",
                (run_id, ))

            ret_val = []

            for record in curs:
                ret_val.append(record[0])


        return ret_val

    def getMaxFoodAtGeneration(self, run_ids, generation):
        with self.__getCursor() as curs:
            curs.execute("""SELECT MAX(food_max) AS food_max
                FROM generations
                WHERE generation=%s AND
                run_id IN %s;""", (generation - 1, tuple(run_ids), ) )

            ret_val = curs.fetchall()[0][0]

        return ret_val


    def getNetworkByID(self, network_id):
        with self.__getCursor() as curs:
            curs.execute("""SELECT net
                FROM networks
                WHERE id=%s;""", (network_id, ) )

            results = curs.fetchall()

        if not results:
            print "No network was found for network_id {0}".format(network_id)
            raise NetworkNotFound(network_id)


        ret_sio = StringIO.StringIO(results[0][0])

        ret_net = pickle.load(ret_sio)

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

        with self.__getCursor() as curs:
            curs.execute(query_str, (generation, run_ids) )

            ret_val = curs.fetchall()[0][0]

        return ret_val


    def getStatAverageRunIds(self, run_ids, generation=199,
        group="food", stat="max"):
        """ Provided a tuple of run_ids, returns the average requested
        stat in the given group.

        Returns:
            Decimal: With average of requested query.

        """

        if group != "food" and group != "moves":
            print "ERROR: Invalid type ({0}) of group requested!".format(group)
            return

        if (stat != "max" and stat != "min" and
            stat != "avg" and stat != "stddev_pop"):
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
        elif stat == "stddev_pop":
            query_str = """SELECT STDDEV_POP({0}::numeric)
                FROM generations
                WHERE
                    generation=%s AND
                    run_id IN %s;""".format(sel_str)

        with self.__getCursor() as curs:
            curs.execute(query_str, (generation, run_ids) )

            ret_val = curs.fetchall()[0][0]

        return ret_val


    def getStatAverageLikeRunId(self, run_id, generation=199,
        group="food", stat="max"):
        """ Given a run_id, returns the average of the requested stat
        in the requested group. This function merely does the lookup of the
        getSameRunIDs as a convinence and calls getStatAverageRunIds.

        """

        run_ids = tuple(self.getSameRunIDs(run_id))

        return self.getStatAverageRunIds(run_ids, generation, group, stat)


    def getFirstRunId(self, net, gen, pop, trail=3, max_moves=325,
        mutate_id=1, elite_count=3, p_mutate=0.2,
        p_crossover=0.5, weight_min=-5.0, weight_max=5.0):
        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        with self.__getCursor() as curs:
            curs.execute("""SELECT run.id
                FROM run
                INNER JOIN run_config
                ON run.run_config_id = run_config.id
                WHERE
                run_config.networks_id = %s AND
                run_config.trails_id = %s AND
                run_config.mutate_id = %s AND
                run_config.generations = %s AND
                run_config.population = %s AND
                run_config.moves_limit = %s AND
                run_config.elite_count = %s AND
                round(run_config.p_mutate::numeric, 4) = %s AND
                round(run_config.p_crossover::numeric, 4) = %s AND
                run_config.weight_min = %s AND
                run_config.weight_max = %s
                LIMIT 1;""", (
                    net,
                    trail,
                    mutate_id,
                    gen,
                    pop,
                    max_moves,
                    elite_count,
                    p_mutate,
                    p_crossover,
                    weight_min,
                    weight_max
                ))

            try:
                ret_val = curs.fetchall()[0][0]
            except IndexError:
                # Means we found nothing matching.
                # Clean up and print some debug information.
                curs.close()
                conn.close()

                print "ERROR: Failed to find a match on query!"
                print "net         = {0}".format(net)
                print "trail       = {0}".format(trail)
                print "mutate_id   = {0}".format(mutate_id)
                print "generations = {0}".format(gen)
                print "pop         = {0}".format(pop)
                print "max_moves   = {0}".format(max_moves)
                print "elite_count = {0}".format(elite_count)
                print "p_mutate    = {0}".format(p_mutate)
                print "p_crossover = {0}".format(p_crossover)
                print "weight_min  = {0}".format(weight_min)
                print "weight_max  = {0}".format(weight_max)

                raise


        curs.close()
        conn.close()

        return ret_val


    @staticmethod
    def __build_where_filters(filters=None, table="run_config"):
        """ Takes a given set of filters and builds a SQL ready
        WHERE statement (or statements for multiple filters) and returns
        a string ready for variable substitution in psycopg2 cursor
        execute.

        Returns:
            str. A string of the WHERE part of query.
        """

        start_filter = True
        filter_str = ""

        if table == "run_config":
            valid_cols = VALID_COLUMNS.RUN_CONFIG


        for curr_key in filters.iterkeys():
            this_s = ""

            if start_filter:
                this_s += "WHERE "
                start_filter = False
            else:
                this_s += "AND "

            if curr_key in valid_cols:
                filter_str += this_s + "{0} = %s\n".format(curr_key)

        return filter_str


    def table_listing(
            self,
            filters=None):

        if filters == None:
            filters = {"generations" : 200}

        where_str = DBUtils.__build_where_filters(filters)

        # Build the base query string with the sort column plugged in.
        data_query_str = """SELECT id, trails_id, networks_id, generations,
            population, moves_limit, elite_count, mutate_id,
            p_mutate, p_crossover, weight_min, weight_max
            FROM   run_config
            {0}""".format(where_str)

        # Run the query and get the data table.
        with self.__getCursor() as curs:
            curs.execute(data_query_str, filters.values())

            run_config_l = curs.fetchall()

        ret_val = []

        # Now, add the run IDs matching the run IDs.
        for curr_run_info in run_config_l:
            result = self.getRunsWithConfigID(curr_run_info[0])

            joined_list = curr_run_info + (list(result), )

            ret_val.append(joined_list)


        return ret_val


    def getRunsWithConfigID(self, config_id):
        """ Takes a configuration id and returns all of the run_ids that
        were ran with this configuration.

        Returns:
           list. A list of run_id (as int) that have same configuration_id.

        """
        query_str = """SELECT ARRAY(SELECT id
        FROM run
        WHERE run_config_id = %s);"""

        with self.__getCursor() as curs:
            curs.execute(query_str, (config_id, ))

            ret_val = curs.fetchall()[0][0]

        return ret_val


    def fetchConfigInfo(self, config_id):
        """ Takes a config_id and returns a dictionary with the
        parameters used on this run.

        Returns:
            dict. Of the configuration used on this run.

        """

        with self.__getCursor() as curs:
            curs.execute("""SELECT
                trails_id,
                networks_id,
                mutate_id,
                generations,
                population,
                moves_limit,
                elite_count,
                p_mutate,
                p_crossover,
                weight_min,
                weight_max
                FROM run_config
                WHERE id = %s;""", (config_id, ) )

            result = curs.fetchall()[0]

            curr_dict                    = {}

            curr_dict["trails_id"]       = result[0]
            curr_dict["networks_id"]     = result[1]
            curr_dict["mutate_id"]       = result[2]
            curr_dict["generations"]     = result[3]
            curr_dict["population"]      = result[4]
            curr_dict["moves_limit"]     = result[5]
            curr_dict["elite_count"]     = result[6]
            curr_dict["p_mutate"]        = result[7]
            curr_dict["p_crossover"]     = result[8]
            curr_dict["weight_min"]      = result[9]
            curr_dict["weight_max"]      = result[10]


        return curr_dict


    def fetchConfigRunsInfo(self, config_id):
        """ Generates a table with run_id, run_date, best food, and
        best moves with a provided config_id. Returns the results a list
        containing a dictionary of the items.

        Returns:
           list. A list containing dictionaries of the items above with
           keys of id, run_date, food, moves.

        """
        with self.__getCursor() as curs:
            curs.execute("""SELECT
                run.id,
                run.run_date,
                run.debug,
                MAX(generations.food_max),
                MIN(moves_min)
                FROM run
                INNER JOIN generations
                ON run.id = generations.run_id
                WHERE run.id IN (
                    SELECT id
                    FROM run
                    WHERE run_config_id = %s)
                GROUP BY run.id
                ORDER BY run.id;""",
                (config_id, ))

            ret_val = []

            for record in curs:
                temp_dict              = {}
                temp_dict["id"]        = record[0]
                temp_dict["run_date"]  = record[1]
                temp_dict["debug"]     = record[2]
                temp_dict["food"]      = record[3]
                temp_dict["moves"]     = record[4]

                ret_val.append(temp_dict)

        return ret_val

    def getRunBest(self, run_ids):
        """ Takes a set of run_ids and returns a dictionary with the
        best food and best moves in a dictionary with run_id as key.

        Returns:
            dict. A dictionary with run_id as keys containing a dictionary
                with keys "food" and "moves" for best (max, min),
                respectively.

        """
        with self.__getCursor() as curs:
            curs.execute("""SELECT
                run_id,
                MAX(generations.food_max),
                MIN(moves_min)
                FROM generations
                WHERE run_id IN %s
                GROUP BY run_id;""",
                tuple(run_ids))

            ret_val = {}

            for record in curs:
                temp_dict  = {}
                temp_dict["food"]  = record[1]
                temp_dict["moves"] = record[2]

                ret_val[record[0]] = temp_dict

        return ret_val




