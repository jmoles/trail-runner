from pybrain.structure import FeedForwardNetwork, LinearLayer, SigmoidLayer, FullConnection, RecurrentNetwork
import numpy as np

class NetworkTypes:
    JEFFERSON = 0
    JEFF_M_DL_10_5_4_V1 = 1
    STRINGS = [
        "Jefferson 2,5,4 NN v1",
        "Jefferson-like MDL5 10,5,4 NN v1"
    ]

class AgentNetwork:
    def __init__(self, network_type=NetworkTypes.JEFFERSON):
        self.network_type = network_type
        self.__network_string = NetworkTypes.STRINGS[self.network_type]

        self.__history = []

        if self.network_type == NetworkTypes.JEFF_M_DL_10_5_4_V1:
            # Initalize the history with all trues
            for _ in range(0,5):
                self.__history.append(False)

            # Build a delay line neural network.
            self.network = FeedForwardNetwork()

            inLayer = LinearLayer(10)
            hiddenLayer = SigmoidLayer(5)
            outputLayer = LinearLayer(4)

            self.network.addInputModule(inLayer)
            self.network.addModule(hiddenLayer)
            self.network.addOutputModule(outputLayer)

            self.in_to_hidden     = FullConnection(inLayer, hiddenLayer)
            self.in_to_out        = FullConnection(inLayer, outputLayer)
            self.hidden_to_out    = FullConnection(hiddenLayer, outputLayer)

            self.network.addConnection(self.in_to_hidden)
            self.network.addConnection(self.hidden_to_out)
            self.network.addConnection(self.in_to_out)

            self.network.sortModules()

            self.__params_length = len(self.network.params)

        else:
            # Build a neural network.
            self.network = RecurrentNetwork()

            inLayer = LinearLayer(2)
            hiddenLayer = SigmoidLayer(5)
            outputLayer = LinearLayer(4)

            self.network.addInputModule(inLayer)
            self.network.addModule(hiddenLayer)
            self.network.addOutputModule(outputLayer)

            self.in_to_hidden     = FullConnection(inLayer, hiddenLayer)
            self.in_to_out        = FullConnection(inLayer, outputLayer)
            self.hidden_to_out    = FullConnection(hiddenLayer, outputLayer)
            self.hidden_to_hidden = FullConnection(hiddenLayer, hiddenLayer)

            self.network.addConnection(self.in_to_hidden)
            self.network.addConnection(self.hidden_to_out)
            self.network.addConnection(self.in_to_out)
            self.network.addRecurrentConnection(self.hidden_to_hidden)

            self.network.sortModules()

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
        if self.network_type == NetworkTypes.JEFFERSON:
            result = 0
            if trailAhead == True:
                result = self.network.activate([1, 0])
            else:
                result = self.network.activate([0, 1])

            return np.argmax(result)

        elif self.network_type == NetworkTypes.JEFF_M_DL_10_5_4_V1:
            result = 0
            history_numeric = []

            # Update the history
            self.__history.insert(0, trailAhead)
            del self.__history[5:]

            for curr_h in self.__history:
                if curr_h == True:
                    history_numeric.extend([1, 0])
                else:
                    history_numeric.extend([0, 1])


            result = self.network.activate(history_numeric)



            return np.argmax(result)






    def printWeights(self):
        """ Prints the weights for the network.
        """

        print "Input to Hidden"
        print self.in_to_hidden.params

        print ""
        print "Input to Output"
        print self.in_to_out.params

        print ""
        print "Hidden to Output"
        print self.hidden_to_out.params


    def getParamsLength(self):
        return self.__params_length


    def getStringName(self):
        return self.__network_string


