import sys

import mainWindow

if __name__ == "__main__":
    app = mainWindow.guiStructure.QtWidgets.QApplication(sys.argv)
    MainWindow = mainWindow.MainWindow(app)
    MainWindow.show()

    sys.exit(app.exec_())
