from deap import tools
import json
import subprocess
import zmq
from zmq import ssh
from PySide import QtCore, QtGui
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class Communicate(QtCore.QObject):
    newProg       = QtCore.Signal(int)
    newIndividual = QtCore.Signal(list)
    newGen        = QtCore.Signal(str)

class AgentGA(QtCore.QThread):

    def __init__(self, bar=None, gen_label=None):
        super(AgentGA, self).__init__()
        self.filename   = ""
        self.moves      = 0
        self.pop_size   = 0
        self.gens       = 0
        self.auto_run   = 0

        # Communicate class
        self.c          = Communicate()

        self.bar        = bar
        self.gen_label  = gen_label

        # Connect the signal/slot for the progress bar
        self.c.newProg[int].connect(self.bar.setValue)
        self.c.newGen[str].connect(self.gen_label.setText)

        self.proc       = ()

        # Variable to say if processing should run
        self.__abort    = False
        self.mutex      = QtCore.QMutex()

    def __exit__(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait()

    def setVars(self, filename, moves, pop, gens, auto_run):
        self.filename   = filename
        self.moves      = moves
        self.pop_size   = pop
        self.gens       = gens
        self.auto_run   = auto_run

    def run(self):
        self.mutex.lock()
        self.__abort = False
        self.mutex.unlock()
        self.__runMaze()

    def stop(self):
        self.mutex.lock()
        self.__abort = True
        self.mutex.unlock()

    def __runMaze(self):
        # Configure a logbook object
        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "food", "moves"
        logbook.chapters["food"].header = "min", "avg", "max", "std"
        logbook.chapters["moves"].header = "min", "avg", "max", "std"

        # Set up a ZMQ to send informaton to each of the processes.
        HOST_RUN = "tcp://*:9855"

        cmd_list = []
        cmd_list.append("python")
        cmd_list.extend(["-m", "scoop"])
        cmd_list.extend(["--hosts", "home-remote"])
        #cmd_list.extend(["--hostfile", "hosts.txt"])
        #cmd_list.extend(["-p", "/u/jmoles/workspace/tlab/python"])
        cmd_list.extend(["-p", "/home/josh/Dropbox/GitHub/jmoles/python"])
        # cmd_list.extend(["-n", "48"])
        cmd_list.extend(["-n", "8"])
        cmd_list.extend(["--python-interpreter", "/usr/bin/python"])
        cmd_list.append("ga_runner.py")
        cmd_list.extend(["-g", str(self.gens)])
        cmd_list.extend(["-p", str(self.pop_size)])
        cmd_list.extend(["-m", str(self.moves)])
        self.proc = subprocess.Popen(cmd_list)

        # Set up ZMQ push/pull
        HOST        = "tcp://puma.joshmoles.com:9854"
        context     = zmq.Context()
        receiver    = context.socket(zmq.PULL)
        zmq.ssh.tunnel.tunnel_connection(receiver, HOST, "puma.joshmoles.com:7862")

        while not self.__abort:
            json_data = receiver.recv_json()

            if json_data:
                # Record the data in the logbook
                logbook.record(gen=json_data["current_generation"],
                    evals=json_data["current_evals"], **json_data["record"])

                # Update the GUI progress bar and labels.
                self.c.newProg.emit(json_data["progress_percent"])
                self.c.newGen.emit(str(json_data["current_generation"]))

                if json_data["done"]:
                    self.c.newIndividual.emit(json_data["top_dog"])
                    print "Processing complete!"
                    break
                else:
                    if (json_data["current_generation"] %
                            self.auto_run == 0):
                        self.c.newIndividual.emit(json_data["top_dog"])
            else:
                print "Something is wrong with the JSON data."

        self.__plotData(logbook)

        if self.__abort:
            print "Aborted!"

            # Kill the subprocess.
            if self.proc:
                print "Attempting to kill subprocess."
                self.proc.terminate()
                retval = self.proc.poll()
                if retval == None:
                    print "Waiting on subprocess..."
                    self.proc.wait()
                    print "Subprocess killed"
                else:
                    print "Subprocess killed"


    def __plotData(self, logbook):
        gen        = logbook.select("gen")
        moves_avgs = logbook.chapters["moves"].select("avg")
        food_avgs  = logbook.chapters["food"].select("avg")

        fig, ax1 = plt.subplots()
        line1 = ax1.plot(gen, moves_avgs, "b-", label="Average Moves")
        ax1.set_xlabel("Generation")
        ax1.set_ylabel("Moves", color="b")
        for tl in ax1.get_yticklabels():
            tl.set_color("b")

        ax2 = ax1.twinx()
        line2 = ax2.plot(gen, food_avgs , "r-", label="Average Food")
        ax2.set_ylabel("Food", color="r")
        for tl in ax2.get_yticklabels():
            tl.set_color("r")

        lns = line1 + line2
        labs = [l.get_label() for l in lns]

        plt.savefig("test")
