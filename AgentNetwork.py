from pybrain.structure import FeedForwardNetwork, LinearLayer, SigmoidLayer, FullConnection, RecurrentNetwork
import numpy as np  

class AgentNetwork:
    def __init__(self):
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
        result = 0
        if trailAhead == True:
            result = self.network.activate([1, 0])
        else:
            result = self.network.activate([0, 1])

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

        

