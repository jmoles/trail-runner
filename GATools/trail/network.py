from pybrain.structure import FeedForwardNetwork, LinearLayer, SigmoidLayer, FullConnection, RecurrentNetwork

from pybrain.structure.networks.feedforward import FeedForwardNetworkComponent

import numpy as np

try:
    import cPickle as pickle
except:
    import pickle

from ..DBUtils import DBUtils

class network:
    def __init__(self):
        pgdb                 = DBUtils()
        self.__params_length = 0


    def readNetwork(self, network_type):
        self.network         = pgdb.getNetworkByID(network_type)
        self.__params_length = len(self.network.params)

    def readNetworkInstant(self, pb_network):
        self.network         = pb_network
        self.__params_length = len(self.network.params)

    def readNetworkFromFile(self, filename):
        with open(filename, 'r') as f:
            self.network         = pickle.load(f)
        self.__params_length = len(self.network.params)

    def determineMove(self, trailAhead):
        """ Returns the move the agent should make.

        Args:
            trailAhead (bool): True if there is trail/food ahead of agent.

        Returns:
            int. The next move to make::

                0 -- No operation
                1 -- Turn left
                2 -- Turn right
                3 -- Move forward

        """

        if trailAhead == True:
            result = self.network.activate([1, 0])
        else:
            result = self.network.activate([0, 1])

        if (len(result) == 3):
            return (np.argmax(result) + 1)
        else:
            return np.argmax(result)

    def updateParameters(self, new_params):
        self.network._setParameters(new_params)

    def getParamsLength(self):
        return self.__params_length

    @staticmethod
    def createJeffersonStyleNetwork(
        in_count=2,
        hidden_count=5,
        output_count=4,
        recurrent=True,
        in_to_out_connect=True,
        name=None):
        """
        Creates a Jefferson-esque neural network for trail problem.


        Returns:
            pybrain.network. The neural network.

        """

        if recurrent:
            ret_net = RecurrentNetwork(name=name)
        else:
            ret_net = FeedForwardNetwork(name=name)

        in_layer = LinearLayer(in_count, name="food")
        hidden_layer = SigmoidLayer(hidden_count, name="hidden")
        output_layer = LinearLayer(output_count, name="move")

        ret_net.addInputModule(in_layer)
        ret_net.addModule(hidden_layer)
        ret_net.addOutputModule(output_layer)

        in_to_hidden     = FullConnection(in_layer, hidden_layer)
        hidden_to_out    = FullConnection(hidden_layer, output_layer)

        ret_net.addConnection(in_to_hidden)
        ret_net.addConnection(hidden_to_out)

        if in_to_out_connect:
            in_to_out        = FullConnection(in_layer, output_layer)
            ret_net.addConnection(in_to_out)

        if recurrent:
            hidden_to_hidden = FullConnection(hidden_layer, hidden_layer)
            ret_net.addRecurrentConnection(hidden_to_hidden)

        ret_net.sortModules()

        return ret_net


    @staticmethod
    def createJeffersonMDLNetwork(
        mdl_length=2,
        hidden_count=5,
        output_count=4,
        in_to_out_connect=True,
        name=None):

        ret_net = RecurrentNetwork(name=name)

        # Add some components of the neural network.
        hidden_layer = SigmoidLayer(hidden_count, name="hidden")
        output_layer = LinearLayer(output_count, name="move")

        ret_net.addModule(hidden_layer)
        ret_net.addOutputModule(output_layer)

        ret_net.addConnection(
            FullConnection(
                hidden_layer,
                output_layer,
                name="Hidden to Move Layer"))

        mdl_prev = ()

        for idx in range(0, mdl_length):
            # Create the layers
            food_layer = LinearLayer(2, name="Food {0}".format(idx))
            mdl_layer = LinearLayer(2, name="MDL Layer {0}".format(idx))

            # Add to network
            ret_net.addModule(food_layer)
            if idx == 0:
                ret_net.addInputModule(mdl_layer)
            else:
                ret_net.addModule(mdl_layer)
                # Add delay line connection.
                ret_net.addRecurrentConnection(
                    FullConnection(
                        mdl_prev,
                        mdl_layer,
                        name="Recurrent DL {0} to DL {1}".format(idx - 1, idx)))

            # Add connections for
            # - Delay line to NN.
            # - NN to Hidden.
            # - NN to Out (if desired).
            ret_net.addConnection(
                FullConnection(
                    mdl_layer,
                    food_layer,
                    name="DL {0} to Food {0}".format(idx)))
            ret_net.addConnection(
                FullConnection(
                    food_layer,
                    hidden_layer,
                    name="Food {0} to Hidden".format(idx)))
            if in_to_out_connect:
                ret_net.addConnection(
                    FullConnection(
                        food_layer,
                        output_layer,
                        name="Food {0} to Output".format(idx)))

            mdl_prev = mdl_layer

        ret_net.sortModules()

        return ret_net
