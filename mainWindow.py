import os

from PIL.ImageQt import ImageQt
from skimage.io import imread
from scipy.misc import toimage

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPixmap, QImage

import pydicom
from pydicom.data import get_testdata_files

import numpy as np
import math

import guiStructure
import processing


class MainWindow(guiStructure.QtWidgets.QWidget, guiStructure.Ui_MainWindow):
    input_image = None
    sinogram = None
    output_image = None
    cvImage = None

    new_process = None

    iterative = False
    filter = False

    app = None

    def __init__(self, app, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.showMaximized()

        self.pushButton_apply.setEnabled(False)

        self.pushButton_apply.clicked.connect(self.on_click_apply)
        self.pushButton_browse.clicked.connect(self.on_click_browse)
        self.pushButton_save.clicked.connect(self.on_click_save)

        self.checkBox_iterative.stateChanged.connect(self.click_box_iterative)
        self.checkBox_filter.stateChanged.connect(self.click_box_filter)

        self.app = app

    @pyqtSlot()
    def on_click_apply(self):
        step_val = float(self.lineEdit_step.text().strip())
        n_val = int(self.lineEdit_n.text().strip())
        l_val = float(self.lineEdit_width.text().strip())

        self.new_process = processing.Processing(step_val, n_val, l_val, self.cvImage, self)
        self.new_process.radon()

        self.new_process.reverse_radon()

        if self.filter:
            self.new_process.filtering()
            self.new_process.rmse()

        else:
            self.new_process.rmse()

        if self.iterative:
           self.label_statistic.setText("Błąd średniokwadratowy: " + str(self.new_process.rmse))

        else:
            self.sinogram = toimage(self.new_process.sinogram)
            qsinogram = ImageQt(self.sinogram)

            self.output_image = toimage(self.new_process.newImage)
            qoutput = ImageQt(self.output_image)

            pixmap1 = QPixmap.fromImage(qsinogram)
            pixmap2 = QPixmap.fromImage(qoutput)

            pixmap1 = pixmap1.scaled(self.label_img_sin.size(), Qt.KeepAspectRatio)
            pixmap2 = pixmap2.scaled(self.label_img_out.size(), Qt.KeepAspectRatio)

            self.label_img_sin.setPixmap(pixmap1)
            self.label_img_out.setPixmap(pixmap2)

            self.label_statistic.setText("Błąd średniokwadratowy: " + str(self.new_process.rmse))

    @pyqtSlot()
    def on_click_browse(self):
        self.input_image, _ = QFileDialog.getOpenFileName(self, 'Open file', "*.jpg")

        self.cvImage = imread(self.input_image, as_gray=True)
        pixmap = QPixmap(self.input_image)

        if self.input_image != "":
            self.label_img_in.setPixmap(pixmap.scaled(self.label_img_in.size(), Qt.KeepAspectRatio))
            self.pushButton_apply.setEnabled(True)

    @pyqtSlot()
    def on_click_save(self):
        name = self.lineEdit_name.text().strip()
        surname = self.lineEdit_surname.text().strip()
        id = self.lineEdit_id.text().strip()
        date = self.dateEdit.text()
        comment = self.plainTextEdit.toPlainText()

        dirname = name + "_" + surname
        filepath = dirname + "/" + "dane.txt"

        if not os.path.exists(dirname):
            os.mkdir(dirname)

        f = open(filepath, "w")
        f.write("Imię: " + name + '\n')
        f.write("Nazwisko: " + surname + '\n')
        f.write("PESEL: " + id + '\n')
        f.write("Data badania: " + date + '\n')
        f.write("Komentarz: " + comment + '\n')
        f.close()

        numpy_array = np.array(self.new_process.newImage)

        filename = get_testdata_files("CT_small.dcm")[0]

        ds = pydicom.dcmread(filename)

        ds.PatientName = surname
        ds.StudyDate = date
        ds.PatientComments = comment
        ds.Columns = numpy_array.shape[0]
        ds.Rows = numpy_array.shape[1]

        numpy_array = numpy_array * 16
        print(numpy_array.dtype)
        print(numpy_array.max())
        if numpy_array.dtype != np.uint16:
            numpy_array = numpy_array.astype(np.uint16)
            print("test2")

        ds.PixelData = numpy_array.tobytes()
        ds.save_as(dirname + "/" + "ct_output.dcm")

    def clear_all(self):
        self.lineEdit_step.clear()
        self.lineEdit_n.clear()
        self.lineEdit_width.clear()
        self.checkBox_iterative.setChecked(False)
        self.checkBox_filter.setChecked(False)
        self.lineEdit_name.clear()
        self.lineEdit_surname.clear()
        self.lineEdit_id.clear()
        self.plainTextEdit.clear()
        self.label_img_in.clear()
        self.label_img_sin.clear()
        self.label_img_out.clear()
        self.label_statistic.clear()

        self.input_image = None
        self.sinogram = None
        self.output_image = None
        self.cvImage = None
        self.new_process = None

        self.iterative = False
        self.filter = False

        self.pushButton_apply.setEnabled(False)

    def click_box_iterative(self, state):
        if state == Qt.Checked:
            self.iterative = True

        else:
            self.iterative = False

    def click_box_filter(self, state):
        if state == Qt.Checked:
            self.filter = True

        else:
            self.filter = False

    def to2DArray(self, pixel_arr):
        tab = []
        for a in range(3):
            for i in range(pixel_arr.shape[0]):
                for j in range(pixel_arr.shape[1]):
                    tab.append(math.floor(pixel_arr[i][j][0]))
        return tab