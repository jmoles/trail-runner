from contextlib import contextmanager
import json
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


class NetworkNotFound(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class DBUtils(object):
    def __init__(self, config_file, debug=False):

        with open(config_file) as fh:
            config = json.load(fh)
        self.__dsn = (
            "host={0} dbname={1} user={2} port={3} password={4}".format(
                config["database"]["host"],
                config["database"]["db"],
                config["database"]["user"],
                config["database"]["port"],
                config["database"]["password"]))

        self.__debug = debug

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

    def getIDs(self):
        # Returns a list of network, trail, and mutate ids in a dictionary
        # with keys of "trail", "network", "mutate".

        with self.__getCursor() as curs:
            curs.execute("SELECT trails.id, networks.id,"
            "mutate.id, selection.id, variations.id "
            "FROM trails, networks, mutate, selection, variations;")
            results = curs.fetchall()

        return {
            "trail" : list(set([int(i[0]) for i in results])),
            "network" : list(set([int(i[1]) for i in results])),
            "mutate" : list(set([int(i[2]) for i in results])),
            "selection" : list(set([int(i[3]) for i in results])),
            "variations" : list(set([int(i[4]) for i in results])),
        }

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
            selection_id                   = %s AND
            variations_id                  = %s AND
            generations                    = %s AND
            population                     = %s AND
            moves_limit                    = %s AND
            (sel_tourn_size                 = %s OR
             sel_tourn_size                 IS NULL) AND
            round(p_mutate::numeric, 4)    = %s AND
            round(p_crossover::numeric, 4) = %s AND
            weight_min                     = %s AND
            weight_max                     = %s AND
            (lambda                        = %s OR
             lambda                        IS NULL) AND
            algorithm_ver                  = %s AND
            (mean_check_length             = %s OR
             mean_check_length             IS NULL)
            """, (
                run_info["networks_id"],
                run_info["trails_id"],
                run_info["mutate_id"],
                run_info["selection_id"],
                run_info["variations_id"],
                run_info["generations"],
                run_info["population"],
                run_info["moves_limit"],
                run_info["sel_tourn_size"],
                round(run_info["p_mutate"], 4),
                round(run_info["p_crossover"], 4),
                run_info["weight_min"],
                run_info["weight_max"],
                run_info["lambda"],
                run_info["algorithm_ver"],
                run_info["mean_check_length"]
        ))

        # If no row is found, need to add it and get id.
        if curs.rowcount < 1:
            if self.__debug:
                print "DEBUG: Row did not exist. Would have inserted row."

            curs.execute("""INSERT INTO run_config (
                    networks_id,
                    trails_id,
                    mutate_id,
                    selection_id,
                    variations_id,
                    generations,
                    population,
                    moves_limit,
                    sel_tourn_size,
                    p_mutate,
                    p_crossover,
                    weight_min,
                    weight_max,
                    lambda,
                    algorithm_ver,
                    mean_check_length
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s)
                RETURNING id;""", (
                    run_info["networks_id"],
                    run_info["trails_id"],
                    run_info["mutate_id"],
                    run_info["selection_id"],
                    run_info["variations_id"],
                    run_info["generations"],
                    run_info["population"],
                    run_info["moves_limit"],
                    run_info["sel_tourn_size"],
                    run_info["p_mutate"],
                    run_info["p_crossover"],
                    run_info["weight_min"],
                    run_info["weight_max"],
                    run_info["lambda"],
                    run_info["algorithm_ver"],
                    run_info["mean_check_length"]
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

        return run_id


    def getTrailData(self, trailID):
        with self.__getCursor() as curs:
            curs.execute("""SELECT trail_data, name, init_rot FROM trails
                WHERE id=%s;""", (trailID, ))

            curs_results = curs.fetchall()[0]

        return np.matrix(curs_results[0]), curs_results[1], curs_results[2]

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


    def get_elite(self, run_id, generation=None):
        """ Takes a given run and returns the elite individual at that
        generation.

        Args:
            run_id: Run ID to fetch the elite from.
            generation: Generation to fetch elite from, optional. Defaults
                           to the last generation is not specified.

        Returns:
            The elite individual from the specified run as a numpy array.

        """
        with self.__getCursor() as curs:
            if generation is None:
                curs.execute("""SELECT elite
                    FROM generations
                    WHERE run_id = %s
                    AND generation = (
                        SELECT MAX(generation)
                        FROM generations
                        WHERE run_id = %s);
                    """, (run_id, run_id))
            else:
                curs.execute("""SELECT elite
                    FROM generations
                    WHERE run_id = %s
                    AND generation = %s;
                    """, (run_id, generation))

            result = curs.fetchall()

        return np.array(result[0][0])


    def get_run_info(self, run_id):
        """ Returns the configuration on a given run.

        Args:
            run_id: Run ID to fetch run information from.

        Returns:
            A dictionary of the configuration
        """

        with self.__getCursor() as curs:
            curs.execute("""SELECT networks_id, trails_id, moves_limit
                FROM run_config
                WHERE id = (
                    SELECT run_config_id
                    FROM run
                    WHERE id = %s);
                """, (run_id, ))

            result = curs.fetchone()

        return {
            "networks_id" : result[0],
            "trails_id" : result[1],
            "moves_limit" : result[2]
        }
