from PySide import QtCore, QtGui

class Communicate(QtCore.QObject):
    newFile  = QtCore.Signal(str)
    newSpeed = QtCore.Signal(int)

class TrailConf(QtGui.QDockWidget):
    """ Dock widget containing configuration options for Trail.
    """

    def __init__(self, parent):
        super(TrailConf, self).__init__()

        self.setWindowTitle("Configuration")

        self.c = Communicate()

        self.formGroupBox = QtGui.QGroupBox()
        layout = QtGui.QFormLayout()

        # Add an open button to change the maze.
        openButton = QtGui.QPushButton("&Open")
        layout.addRow(QtGui.QLabel("Current Data File"), 
        	openButton)
        openButton.clicked.connect(self.openFile)

        # Add a spin box to control the ant's speed.
        spinBox = QtGui.QSpinBox()
        spinBox.setMinimum(200)
        spinBox.setMaximum(2000)
        spinBox.setSingleStep(100)
        spinBox.setValue(1000)
        layout.addRow(QtGui.QLabel("Speed"), spinBox)
        spinBox.valueChanged[unicode].connect(
        	lambda : self.c.newSpeed.emit(spinBox.value()))

        self.formGroupBox.setLayout(layout)

        self.setWidget(self.formGroupBox)


    def openFile(self):
    	filename, _ = QtGui.QFileDialog.getOpenFileName(self,
            str("Open Data File"), ".", str("Data Files (*.txt *.dat)"))

    	if filename != "":
    		self.c.newFile.emit(filename)
    	

