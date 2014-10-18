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


class NetworkNotFound(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class DBUtils:
    def __init__(
        self,
        host=os.environ.get("PSYCOPG2_DB_HOST", "localhost"),
        db=os.environ.get("PSYCOPG2_DB_DB", "jmoles"),
        user=os.environ.get("PSYCOPG2_DB_USER", "jmoles"),
        password=os.environ.get("PSYCOPG2_DB_PASS", "password"),
        port=os.environ.get("PSYCOPG2_DB_PORT", 5432),
        debug=False):

        self.__dsn = (
            "host={0} dbname={1} user={2} password={3} port={4}".format(
                host, db, user, password, port))

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
            curs.execute("SELECT trails.id, networks.id, mutate.id "
            "FROM trails, networks, mutate;")
            results = curs.fetchall()

        return {
            "trail" : list(set([int(i[0]) for i in results])),
            "network" : list(set([int(i[1]) for i in results])),
            "mutate" : list(set([int(i[2]) for i in results]))
        }

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
