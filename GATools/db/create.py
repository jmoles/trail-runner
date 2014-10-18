try:
    import cPickle as pickle
except:
    import pickle

import os
import psycopg2

from ..trail.network import network


class create:
    def __init__(self, host="db.cecs.pdx.edu", db="jmoles",
        user="jmoles", password=os.environ["PSYCOPG2_DB_PASS"]):

        self.__dsn = "host={0} dbname={1} user={2} password={3}".format(
            host, db, user, password)

    def run(self):
        """ Executes the creation of networks in the database table.
        Designed so more function calls can get added here if necessary."""
        self.__addNetworks()

    def __addNetworks(self,
        table="networks",
        create_table=False):
        """ Adds networks to the specified table. """

        networks_d = tuple(self.__prepareNetworks())

        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        if create_table:
            # Create the table.
            query_s = """CREATE TABLE {0} (
                id serial  NOT NULL,
                name text  NOT NULL,
                net bytea  NOT NULL,
                CONSTRAINT networks_pk PRIMARY KEY (id));""".format(table)

            curs.exeute(query_s)

        # Populate the table.
        query_s = """INSERT INTO {0} (id, name, net)
            VALUES (
                DEFAULT,
                %(name)s,
                %(network)s);""".format(table)

        curs.executemany(query_s, networks_d)

        conn.commit()

        curs.close()
        conn.close()

    def __prepareNetworks(self):
        """ Builds and pickles the tables for DB ready format. """
        ret_d = []

        # Build the neural networks for Jefferson NN and flavors.
        net_d = {}
        net_d["name"]    = "Jefferson NN (2,5,4) v1"
        net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.createJeffersonStyleNetwork(
                    in_count=2,
                    hidden_count=5,
                    output_count=4,
                    recurrent=True,
                    in_to_out_connect=True,
                    name=net_d["name"])))
        ret_d.append(net_d)

        net_d = {}
        net_d["name"]    = "Jefferson NN (2, 5, 3) v1"
        net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.createJeffersonStyleNetwork(
                    in_count=2,
                    hidden_count=5,
                    output_count=3,
                    recurrent=True,
                    in_to_out_connect=True,
                    name=net_d["name"])))
        ret_d.append(net_d)

        net_d = {}
        net_d["name"]    = "Jefferson NN (2, 1, 4) v1"
        net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.createJeffersonStyleNetwork(
                    in_count=2,
                    hidden_count=1,
                    output_count=4,
                    recurrent=True,
                    in_to_out_connect=True,
                    name=net_d["name"])))
        ret_d.append(net_d)

        net_d = {}
        net_d["name"]    = "Jefferson NN (2, 1, 3) v1"
        net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.createJeffersonStyleNetwork(
                    in_count=2,
                    hidden_count=1,
                    output_count=3,
                    recurrent=True,
                    in_to_out_connect=True,
                    name=net_d["name"])))
        ret_d.append(net_d)

        for idx in range(2, 11):
            net_d = {}
            net_d["name"]    = "Jeff-like NN MDL{0} ({1}, 5, 4) v1".format(
                idx, idx * 2)
            net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.createJeffersonMDLNetwork(
                    mdl_length=idx,
                    hidden_count=5,
                    output_count=4,
                    name=net_d["name"])))
            ret_d.append(net_d)

        for idx in range(2, 11):
            net_d = {}
            net_d["name"]    = "Jeff-like NN MDL{0} ({1}, 5, 3) v1".format(
                idx, idx * 2)
            net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.createJeffersonMDLNetwork(
                    mdl_length=idx,
                    hidden_count=5,
                    output_count=3,
                    name=net_d["name"])))
            ret_d.append(net_d)

        for idx in range(2, 11):
            net_d = {}
            net_d["name"]    = "Jeff-like NN MDL{0} ({1}, 1, 4) v1".format(
                idx, idx * 2)
            net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.createJeffersonMDLNetwork(
                    mdl_length=idx,
                    hidden_count=1,
                    output_count=4,
                    name=net_d["name"])))
            ret_d.append(net_d)

        for idx in range(2, 11):
            net_d = {}
            net_d["name"]    = "Jeff-like NN MDL{0} ({1}, 1, 3) v1".format(
                idx, idx * 2)
            net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.createJeffersonMDLNetwork(
                    mdl_length=idx,
                    hidden_count=1,
                    output_count=3,
                    name=net_d["name"])))
            ret_d.append(net_d)

        for idx in range(2, 11):
            net_d = {}
            net_d["name"]    = "JL NN Chemical DL{0} ({1}, 5, 3) v1".format(
                idx, idx * 2)
            net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.create_jefferson_chemical_network(
                    mdl_length=idx,
                    hidden_count=5,
                    output_count=3,
                    name=net_d["name"])))
            ret_d.append(net_d)

        for idx in range(2, 11):
            net_d = {}
            net_d["name"]    = "JL NN Chemical DL{0} ({1}, 1, 3) v1".format(
                idx, idx * 2)
            net_d["network"] = psycopg2.Binary(pickle.dumps(
                network.create_jefferson_chemical_network(
                    mdl_length=idx,
                    hidden_count=1,
                    output_count=3,
                    name=net_d["name"])))
            ret_d.append(net_d)

        return ret_d
