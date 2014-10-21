try:
    import cPickle as pickle
except:
    import pickle

import os
import psycopg2
import textwrap

from ..trail.network import network

class create:
    def __init__(self, host="db.cecs.pdx.edu", db="jmoles",
        user="jmoles", password=os.environ["PSYCOPG2_DB_PASS"]):

        self.__dsn = "host={0} dbname={1} user={2} password={3}".format(
            host, db, user, password)

    @staticmethod
    def generate_network_string(filename="networks.sql", table="networks", create_table=False):
        """ Generates a string of SQL for insertion to database. """

        query_s = ""

        networks_d = tuple()

        if create_table:
            # Create the table.
            query_s += textwrap.dedent("""
                CREATE TABLE {0} (
                id serial  NOT NULL,
                name text  NOT NULL,
                net bytea  NOT NULL,
                dl_length int NOT NULL,
                CONSTRAINT networks_pk PRIMARY KEY (id));

                """.format(table))

        # Populate the table.
        query_s += "INSERT INTO {0} (id, name, net, dl_length) VALUES (".format(table)
        for curr_d in create.__prepareNetworks():
            query_s += "\n    (DEFAULT, {0}, {1}, {2}),".format(
            curr_d["name"],
            curr_d["network"],
            curr_d["dl_length"])

        query_s = query_s.rstrip(",")

        query_s += ");"

        with open(filename, 'w') as fh:
            fh.write(query_s)

    @staticmethod
    def __prepareNetworks():
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
        net_d["dl_length"] = 0
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
        net_d["dl_length"] = 0
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
        net_d["dl_length"] = 0
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
        net_d["dl_length"] = 0
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
            net_d["dl_length"] = idx
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
            net_d["dl_length"] = idx
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
            net_d["dl_length"] = idx
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
            net_d["dl_length"] = idx
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
            net_d["dl_length"] = idx
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
            net_d["dl_length"] = idx
            ret_d.append(net_d)

        return ret_d
