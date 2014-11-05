try:
    import cPickle as pickle
except:
    import pickle

import json
import os
import psycopg2
import textwrap

from ..trail.network import network

class create:
    def __init__(self,
    host=os.environ.get("PGHOST", "localhost"),
    db=os.environ.get("PGDATABASE", "josh"),
    user=os.environ.get("PGUSER", "josh"),
    password=os.environ.get("PGPASSWORD", "password"),
    port=os.environ.get("PGPORT", 5432),
    config_file=None):

        if config_file is not None:
            with open(config_file) as fh:
                config = json.load(fh)
            self.__dsn = (
                "host={0} dbname={1} user={2} port={3} password={4}".format(
                    config["database"]["host"],
                    config["database"]["db"],
                    config["database"]["user"],
                    config["database"]["port"],
                    config["database"]["password"]))
        else:
            self.__dsn = (
                "host={0} dbname={1} user={2} port={3} password={4}".format(
                    host, db, user, port, password))

    def insert_networks(self):
        """ Inserts the networks into the SQL database. """

        query_s = ""

        networks_d = tuple()

        conn = psycopg2.connect(self.__dsn)
        curs = conn.cursor()

        networks_d = create.__prepareNetworks()

        # Populate the table.
        query_s = """INSERT INTO networks
            (id, name, net, dl_length, hidden_count, input_count, output_count, flavor)
            VALUES (
                DEFAULT,
                %(name)s,
                %(network)s,
                %(dl_length)s,
                %(hidden_count)s,
                %(input_count)s,
                %(output_count)s,
                %(flavor)s);"""

        curs.executemany(query_s, networks_d)

        conn.commit()

        curs.close()
        conn.close()

    @staticmethod
    def __prepareNetworks():
        """ Builds and pickles the tables for DB ready format. """
        ret_d = []

        # Build the neural networks for Jefferson NN basic.
        for hidden_neuron in [1, 10]:
            for out_neuron in [3, 4]:
                net_d = {}
                net_d["name"] = "Jefferson NN ({0},{1},{2})".format(
                    2,
                    hidden_neuron,
                    out_neuron
                )
                net_d["network"] = psycopg2.Binary(pickle.dumps(
                        network.createJeffersonStyleNetwork(
                            in_count=2,
                            hidden_count=hidden_neuron,
                            output_count=out_neuron,
                            recurrent=True,
                            in_to_out_connect=True,
                            name=net_d["name"])))
                net_d["dl_length"] = 0
                net_d["hidden_count"] = hidden_neuron
                net_d["input_count"] = 2
                net_d["output_count"] = out_neuron
                net_d["flavor"] = 1
                ret_d.append(net_d)

        # Build the variations of NN/MDL like networks.
        for out_neuron in [3, 4]:
            for hidden_neuron in range(2, 11):
                for dl_length in range(2, 16):
                    net_d = {}
                    net_d["name"] = "Jeff-like NN MDL{0} ({1}, {2}, {3})".format(
                        dl_length, dl_length * 2, hidden_neuron, out_neuron)
                    net_d["network"] = psycopg2.Binary(pickle.dumps(
                        network.createJeffersonMDLNetwork(
                            mdl_length=dl_length,
                            hidden_count=hidden_neuron,
                            output_count=out_neuron,
                            name=net_d["name"])))
                    net_d["dl_length"] = dl_length
                    net_d["hidden_count"] = hidden_neuron
                    net_d["input_count"] = dl_length * 2
                    net_d["output_count"] = out_neuron
                    net_d["flavor"] = 2
                    ret_d.append(net_d)


        return ret_d
