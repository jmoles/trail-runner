from pybrain.structure import FeedForwardNetwork, RecurrentNetwork
from pybrain.structure import LinearLayer, SigmoidLayer, FullConnection

import numpy as np
import re

try:
    import cPickle as pickle
except:
    import pickle

from ..chemistry import DelayLine

class network:
    def __init__(self, debug=False):
        self.__params_length = 0
        self.__chem_network = False
        self.__delay_line = None
        self.__dl_length = 0
        self.network = None

        self.__DEBUG = debug

    def readNetworkFromFile(self, filename):
        with open(filename, 'r') as f:
            self.network         = pickle.load(f)
        self.__process_network()

    def __process_network(self):
        """ Examines the network and configures the class for using it.
        """
        if "Chemical" in self.network.name:
            # This is a chemical delay line.
            chem_re = re.compile(
                "JL NN Chemical DL([0-9]+) \([0-9]+,[0-9]+,[0-9]+\) v[0-9]+")
            self.__dl_length = int(chem_re.findall(self.network.name)[0])
            self.__chem_network = True
            dl_param_count = self.__dl_length * 3
            if self.__DEBUG:
                print "DEBUG: Network is a chemical network."

        else:
            dl_param_count = 0
            if self.__DEBUG:
                print "DEBUG: Network is NOT a chemical network."

        self.__params_length = len(self.network.params) + dl_param_count

        if self.__DEBUG:
            print "DEBUG: Paramters are length {0}.".format(
                self.__params_length)

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

        if self.__chem_network:
            # First, activate the chemical delay line.
            # Then, take the output of the delay line and active the
            # neural network.
            chem_res = self.__delay_line.evaluate(int(trailAhead))

            nn_input = []
            for curr_x in chem_res:
                nn_input.append(curr_x)
                nn_input.append(1 - curr_x)

            result = self.network.activate(nn_input)
        else:
            if trailAhead == True:
                result = self.network.activate([1, 0])
            else:
                result = self.network.activate([0, 1])

        if (len(result) == 3):
            return (np.argmax(result) + 1)
        else:
            return np.argmax(result)

    def updateParameters(self, new_params):
        if self.__chem_network:
            # Create the chemistry delay line and pass the rest
            # of the parameters to the neural network.
            self.__delay_line = DelayLine(
                rate_constants=abs(np.reshape(
                    new_params[-3 * self.__dl_length:],(self.__dl_length,3))),
                user_interactive=False)

            self.network._setParameters(new_params[:-3 * self.__dl_length])
        else:
            self.network._setParameters(new_params)

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

    @staticmethod
    def create_jefferson_chemical_network(
        mdl_length=2,
        hidden_count=5,
        output_count=3,
        in_to_out_connect=True,
        name=None):

        if not name:
            name = "JL NN Chemical DL{0} ({1},{2},{3}) v1".format(
                mdl_length,
                mdl_length * 2,
                hidden_count,
                output_count)


        ret_net = network.createJeffersonStyleNetwork(
            in_count=mdl_length * 2,
            hidden_count=hidden_count,
            output_count=output_count,
            recurrent=True,
            in_to_out_connect=in_to_out_connect,
            name=name)

        return ret_net
