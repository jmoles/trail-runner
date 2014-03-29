import json
import os
import pickle
import re
import subprocess
import zmq
from PySide import QtCore, QtGui

class Communicate(QtCore.QObject):
    newProg       = QtCore.Signal(int)
    newIndividual = QtCore.Signal(list)
    newGen        = QtCore.Signal(str)

class AgentGA(QtCore.QThread):

    CHECKPOINT = "checkpoint.pkl"
    PICKLE_VER = 1

    def __init__(self, bar=None, gen_label=None):
        super(AgentGA, self).__init__()
        self.filename   = ""
        self.moves      = 0
        self.pop_size   = 0
        self.gens       = 0

        # Communicate class
        self.c          = Communicate()

        self.bar        = bar
        self.gen_label  = gen_label

        # Connect the signal/slot for the progress bar
        self.c.newProg[int].connect(self.bar.setValue)
        self.c.newGen[str].connect(self.gen_label.setText)

        self.proc       = ()

    def __exit__(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait()

    def setVars(self, filename, moves, pop, gens):
        self.filename   = filename
        self.moves      = moves
        self.pop_size   = pop
        self.gens       = gens

    def run(self):
        self.__abort = False
        self.__runMaze(AgentGA.CHECKPOINT)

    def stop(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait()

    def __parseMessage(self, message):
        match     = re.search('tcp://\*:9854 : (.*)', message)

        if match:
            return json.loads(match.group(1))
        else:
            return None

    def __runMaze(self, checkpoint=None):
        # self.proc = subprocess.Popen(["python", "-m", "scoop", "-n", "2",
        #     "ga_runner.py",
        #     "-g", str(self.gens),
        #     "-p", str(self.pop_size),
        #     "-m", str(self.moves)], stdout=subprocess.PIPE)

        cmd_list = []
        cmd_list.append("python")
        cmd_list.extend(["-m", "scoop"])
        cmd_list.extend(["--hosts", "home-remote"])
        cmd_list.extend(["-p", "/home/josh/Dropbox/GitHub/jmoles/python/"])
        cmd_list.extend(["-n", "8"])
        cmd_list.extend(["--python-interpreter", "/usr/bin/python"])
        cmd_list.append("ga_runner.py")
        cmd_list.extend(["-g", str(self.gens)])
        cmd_list.extend(["-p", str(self.pop_size)])
        cmd_list.extend(["-m", str(self.moves)])
        self.proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)

        # Use ZMQ to collect information from process.
        HOST    = "tcp://puma.joshmoles.com:9854"
        context = zmq.Context()
        sock    = context.socket(zmq.SUB)
        sock.setsockopt(zmq.SUBSCRIBE, '')

        sock.connect(HOST)

        while True:
            message = sock.recv()
            json_data = self.__parseMessage(message)

            if json_data:
                self.c.newProg.emit(json_data["progress_percent"])
                self.c.newGen.emit(str(json_data["current_generation"]))
                if json_data["done"]:
                    self.c.newIndividual.emit(json_data["top_dog"])
                    print "Processing complete!"
                    break
                else:
                    if json_data["current_generation"] % 20 == 0:
                        self.c.newIndividual.emit(json_data["top_dog"])
            else:
                print "Something is wrong with the JSON data."








