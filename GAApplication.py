import logging
import sys
import time
from numpy import matrix
from PySide import QtCore, QtGui
from deap import algorithms, base, creator, tools

from TrailUI import TrailUI
from AgentGA import AgentGA
from AgentNetwork import AgentNetwork
from AgentTrail import AgentTrail

from GASettings import GASettings

class Communicate(QtCore.QObject):
    newFile  = QtCore.Signal(str)
    newSpeed = QtCore.Signal(int)
    newProg  = QtCore.Signal(int)

class GAApplication(QtGui.QMainWindow):

    def __init__(self):
        super(GAApplication, self).__init__()

        # Configure and open settings
        QtCore.QCoreApplication.setOrganizationName("Josh Moles")
        QtCore.QCoreApplication.setOrganizationDomain("joshmoles.com")
        QtCore.QCoreApplication.setApplicationName("Ant Trail")
        self.settings = GASettings()

        # Variables
        self.settings.beginGroup("trail")
        self.filename = self.settings.value("default_file")
        self.moves    = self.settings.value("moves")
        self.pop_size = self.settings.value("population")
        self.gens     = self.settings.value("generations")
        self.auto_run = self.settings.value("auto_run")
        self.settings.endGroup()

        # UI Elements
        self.moves_box    = ()
        self.pop_box      = ()
        self.gen_box      = ()
        self.auto_run_box = ()
        self.run_button   = ()
        self.reset_button = ()
        self.progress_bar = ()

        self.setWindowTitle('Genetic Algorithm Tools')
        self.c = Communicate()

        self.readSettings()

        self.antTrail = TrailUI(self, self.filename)
        self.antTrail.setContentsMargins(0,0,0,0)

        # Get the handle to the statusbar.
        self.statusbar = self.statusBar()

        # Labels for the progress bar area for current generation
        # and time remaining.
        self.gen_label = QtGui.QLabel()
        self.gen_label.setToolTip("Current Generation")
        self.gen_label.setAlignment(QtCore.Qt.AlignLeft)
        self.gen_label.setMinimumWidth(40)
        self.time_label = QtGui.QLabel()
        self.time_label.setToolTip("Estimated Time Remaining")
        self.time_label.setAlignment(QtCore.Qt.AlignRight)
        self.time_label.setMinimumWidth(65)

        # Create actions
        self.createActions()

        # Create the menu bar
        self.createMenus()

        # Create docks
        self.createDocks()

        # Set up the thread to run Genetic Algorithms
        self.ga_thread  = AgentGA(self.progress_bar, self.gen_label,
            self.time_label)

        # Connect the signals and slots
        self.connectSigSlot()

        self.setCentralWidget(self.antTrail)

        # Set the status bar text to ready.
        self.statusbar.showMessage("Ready")

    def __exit__(self):
        self.ga_thread.stop()
        self.ga_thread.wait()

    def writeSettings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.endGroup()

        self.settings.beginGroup("trail")
        self.settings.setValue("default_file", self.filename)
        self.settings.setValue("moves", self.moves_box.value())
        self.settings.setValue("population", self.pop_box.value())
        self.settings.setValue("generations", self.gen_box.value())
        self.settings.setValue("auto_run", self.auto_run_box.value())
        self.settings.endGroup()

    def readSettings(self):
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size"))
        self.move(self.settings.value("pos"))
        self.settings.endGroup()

    def closeEvent(self, event):
        self.writeSettings()
        QtGui.QMainWindow.closeEvent(self, event)

    def createActions(self):
        self.openTrailAct = QtGui.QAction("&Open Trail...", self,
            shortcut="Ctrl+O", triggered = self.openFile)
        self.exitAct = QtGui.QAction("&Quit", self, triggered=self.close)
        self.gatoolsAct = QtGui.QAction("GA Toolbox", self, checkable = True)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openTrailAct)
        self.fileMenu.addAction(self.exitAct)

        self.toolsMenu = self.menuBar().addMenu("&Tools")
        self.toolsMenu.addAction(self.gatoolsAct)

    def createDocks(self):
        self.settings.beginGroup("trail")

        # Build each of the spin boxes.
        self.moves_box    = QtGui.QSpinBox()
        self.moves_box.setRange(1, 1000)
        self.moves_box.setValue(self.moves)
        self.moves_box.setToolTip(
            "The maixmum number of moves that the agent can make in the maze.")

        self.pop_box      = QtGui.QSpinBox()
        self.pop_box.setRange(1, 1000)
        self.pop_box.setValue(self.pop_size)

        self.gen_box      = QtGui.QSpinBox()
        self.gen_box.setRange(1, 1000)
        self.gen_box.setValue(self.gens)
        self.gen_box.setToolTip(
            "The number of generations to run the optimization for.")

        self.auto_run_box = QtGui.QSpinBox()
        self.auto_run_box.setRange(1, self.gen_box.maximum())
        self.auto_run_box.setValue(self.auto_run)

        self.run_button   = QtGui.QPushButton("Run")
        self.run_button.clicked.connect(self.__runGA)

        self.reset_button      = QtGui.QPushButton("Reset")
        self.reset_button.clicked.connect(self.__resetGADock)

        # Build the GA Settings Dock
        layout       = QtGui.QFormLayout()
        layout.addRow(QtGui.QLabel("Moves"), self.moves_box)
        layout.addRow(QtGui.QLabel("Population"), self.pop_box)
        layout.addRow(QtGui.QLabel("Generations"), self.gen_box)
        layout.addRow(QtGui.QLabel("Auto Run"), self.auto_run_box)
        layout.addRow(self.run_button, self.reset_button)

        content = QtGui.QWidget()
        content.setLayout(layout)

        self.ga_dock    = QtGui.QDockWidget(str("Genetic Algorithm"), self)
        self.ga_dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea |
            QtCore.Qt.LeftDockWidgetArea)
        self.ga_dock.setWidget(content)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.ga_dock)

        # Build the bottom progress dock.
        self.progress_bar = QtGui.QProgressBar()

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.gen_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.time_label)

        content = QtGui.QWidget()
        content.setLayout(layout)

        self.progress_toolbar = QtGui.QToolBar(parent=self)
        self.progress_toolbar.addWidget(content)
        self.progress_toolbar.setFloatable(False)
        self.progress_toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.progress_toolbar)

        self.settings.endGroup()

    def connectSigSlot(self):
        # Connect the signal/slot for the status bar.
        self.antTrail.c.msgToSB[str].connect(self.statusbar.showMessage)

        # Connect the signal/slot for the configuration
        self.c.newFile[str].connect(self.antTrail.loadGrid)

        # Connect the signal/slot for the events when thread starts or stops.
        self.ga_thread.started.connect(self.__setRunStarted)
        self.ga_thread.terminated.connect(self.__setRunTerminated)
        self.ga_thread.finished.connect(self.__setRunFinished)

        # Connect signal/slot for the status bar
        self.c.newProg[int].connect(self.progress_bar.setValue)

        self.ga_thread.c.newIndividual[list].connect(self.__runAgentSlot)

    def openFile(self):
        self.antTrail.pause()
        filename, _ = QtGui.QFileDialog.getOpenFileName(self,
            str("Open Trail File"), "./trails",
            str("Trail Files (*.yml *.yaml)"))

        if filename != "":
            self.c.newFile.emit(filename)
            self.filename = filename
        else:
            # Menu was cancelled. Just resume
            self.antTrail.resume()

    def __runGA(self):
        if(not self.ga_thread.isRunning()):
            # Change what the push button says
            self.run_button.setText("Stop")

            # Read values from the boxes.
            self.moves      = self.moves_box.value()
            self.pop_size   = self.pop_box.value()
            self.gens       = self.gen_box.value()
            self.auto_run   = self.auto_run_box.value()

            self.ga_thread.setVars(self.filename,
                self.moves,
                self.pop_size,
                self.gens,
                self.auto_run)
            self.ga_thread.start()
        else:
            self.ga_thread.stop()

    def __setRunFinished(self):
        self.run_button.setText("Start")
        self.reset_button.setDisabled(False)
        self.c.newProg.emit(100)
        # self.removeToolBar(self.progress_toolbar)

    def __setRunTerminated(self):
        self.run_button.setText("Start")
        self.reset_button.setDisabled(False)
        # self.removeToolBar(self.progress_toolbar)

    def __setRunStarted(self):
        self.run_button.setText("Stop")
        self.reset_button.setDisabled(True)
        self.c.newProg.emit(0)
        self.statusbar.showMessage("Running...")
        # self.addToolBar(self.progress_toolbar)

    def __resetGADock(self):
        self.moves_box.setValue(GASettings.TRAIL_MOVES)
        self.pop_box.setValue(GASettings.TRAIL_POPULATION)
        self.gen_box.setValue(GASettings.TRAIL_GENERATIONS)
        self.auto_run_box.setValue(GASettings.TRAIL_AUTO_RUN)

    @QtCore.Slot(list)
    def __runAgentSlot(self, individual):
        """ Runs the agent through the maze on the GUI with a provided individual.

        Args:
        individual (list): List of float weights used for activation network.
        """
        an    = AgentNetwork()
        at    = AgentTrail()
        moves = ""

        at.readTrail(self.filename)

        an.network._setParameters(individual)

        for _ in xrange(self.moves):

            # First, check if all food was consumed,
            # if so, break.
            if at.getFoodStats()[1] == 0:
                logging.info("All food has been consumed.")
                break

            currMove = an.determineMove(at.isFoodAhead())

            if(currMove == 0):
                # No operation
                moves = moves + "N"
                at.noMove()
            elif(currMove == 1):
                # Turn Left
                moves = moves + "L"
                at.turnLeft()
            elif(currMove == 2):
                # Turn Right
                moves = moves + "R"
                at.turnRight()
            elif(currMove == 3):
                # Move Forward
                moves = moves + "M"
                at.moveForward()


        self.antTrail.loadGrid(self.filename)
        self.antTrail.queueAutoMove(moves)


