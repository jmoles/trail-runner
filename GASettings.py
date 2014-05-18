import logging
from PySide import QtCore, QtGui

class GASettings(QtCore.QSettings):

    VERSION = 6

    # Defaults for items
    TRAIL_MOVES        = 325
    TRAIL_POPULATION   = 300
    TRAIL_GENERATIONS  = 200
    TRAIL_AUTO_RUN     = 30

    def __init__(self):
        self.__configureProgramInfo()

        super(GASettings, self).__init__()

        self.__initSettings()


    def __exit__():
        self.writeSettings()
        self.sync()

    def __configureProgramInfo(self):
        QtCore.QCoreApplication.setOrganizationName("Josh Moles")
        QtCore.QCoreApplication.setOrganizationDomain("joshmoles.com")
        QtCore.QCoreApplication.setApplicationName("Ant Trail")

    def __initSettings(self):

        if int(self.value("version", 0)) != self.VERSION:
            logging.info("User settings is version " +
                str(self.value("version")) +
                " and present settings are at " +
                str(self.VERSION) +
                ". Re-initalizing user settings.")
            # Need to initalize the settings.
            self.clear()

            self.beginGroup("trail")
            self.setValue("moves", 325)
            self.setValue("population", 300)
            self.setValue("generations", 200)
            self.setValue("auto_run", 30)
            self.setValue("trail_num", 3)
            self.setValue("network_idx", 1)
            self.setValue("logging_enabled", 1)
            self.endGroup()

            self.beginGroup("trailUI")
            self.setValue("rect_size", 16)
            self.setValue("agent_delta", 50)
            self.endGroup()

            self.beginGroup("MainWindow")
            self.setValue("size", QtCore.QSize(300, 300))
            self.setValue("pos", QtCore.QPoint(200, 200))
            self.endGroup()

            self.setValue("version", self.VERSION)

            self.sync()
        else:
            logging.debug("Settings are up to date!")


