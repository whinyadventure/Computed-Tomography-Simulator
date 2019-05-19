import math
import numpy as np

from PIL.ImageQt import ImageQt
from scipy.misc import toimage

from bresenham import bresenham

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class Processing:
    mainWindow = None

    deltaAlpha = None
    detectorNumber = None
    detectorRange = None

    image = None
    sinogram = []
    newImage = []

    xEmiterSteps = []
    yEmiterSteps = []
    xDetectorSteps = []
    yDetectorSteps = []

    rmse = None

    def __init__(self, deltaAlpha, detectorNbr, detectorRange, image, window):
        self.deltaAlpha = deltaAlpha
        self.detectorNumber = detectorNbr
        self.detectorRange = detectorRange
        self.image = image
        self.mainWindow = window

    def radon(self):

        radius = math.sqrt(self.image.shape[0] ** 2 + self.image.shape[1] ** 2) / 2.0  # radius

        xCentral = (self.image.shape[1] / 2.0) - 1  # centre coordinates
        yCentral = (self.image.shape[0] / 2.0) - 1

        sinogram_iterative = []

        for i in np.arange(0.0, 180.0, self.deltaAlpha):  # for each emiter step

            xEmiter = radius * math.cos(math.radians(i)) + xCentral  # compute emiter coordinates
            yEmiter = radius * math.sin(math.radians(i)) + yCentral

            xDetector = []
            yDetector = []
            sinogramLine = []

            for n in range(0, self.detectorNumber):  # for each detector compute coordinates
                xDet = radius * math.cos(math.radians(i) + math.pi - (math.radians(self.detectorRange) / 2) +
                                         (n * math.radians(self.detectorRange) / (self.detectorNumber - 1))) + xCentral
                yDet = radius * math.sin(math.radians(i) + math.pi - (math.radians(self.detectorRange) / 2) +
                                         (n * math.radians(self.detectorRange) / (self.detectorNumber - 1))) + yCentral

                xDetector.append(xDet)
                yDetector.append(yDet)

                radiation = 0
                bres = list(bresenham(int(xEmiter), int(yEmiter), int(xDet), int(yDet)))

                for b in bres:
                    if b[0] > -1 and b[0] < self.image.shape[1] and b[1] > -1 and b[1] < self.image.shape[0]:
                        radiation += self.image[b[1]][b[0]]

                sinogramLine.append(radiation)

            self.xEmiterSteps.append(xEmiter)
            self.yEmiterSteps.append(yEmiter)
            self.xDetectorSteps.append(xDetector)
            self.yDetectorSteps.append(yDetector)
            self.sinogram.append(sinogramLine)

            if self.mainWindow.iterative:  # iterative display
                sinogramLine = np.interp(sinogramLine, (np.min(sinogramLine), np.max(sinogramLine)), (0, 255))
                sinogram_iterative.append(sinogramLine)

                helper = toimage(sinogram_iterative)
                qsinogram = ImageQt(helper)

                pixmap1 = QPixmap.fromImage(qsinogram)
                pixmap1 = pixmap1.scaled(self.mainWindow.label_img_sin.width(), self.mainWindow.label_img_sin.height(),
                                         Qt.KeepAspectRatio)

                self.mainWindow.label_img_sin.setPixmap(pixmap1)

                self.mainWindow.app.processEvents()

        self.sinogram = np.interp(self.sinogram, (np.min(self.sinogram), np.max(self.sinogram)), (0, 255))

    def reverse_radon(self):
        self.newImage = self.image.copy()

        if self.mainWindow.iterative:  # iterative display
            iterativeImage = self.image.copy()
            for i in range(len(self.newImage)):
                for n in range(len(self.newImage[i])):
                    iterativeImage[i][n] = 0

        for i in range(len(self.newImage)):
            for n in range(len(self.newImage[i])):
                self.newImage[i][n] = 0

        counter = self.newImage.copy()

        for em in range(0, int(180 / self.deltaAlpha)):  # for each emiter step

            for det in range(0, self.detectorNumber):  # for each detector

                bres = list(
                    bresenham(int(self.xEmiterSteps[em]), int(self.yEmiterSteps[em]), int(self.xDetectorSteps[em][det]),
                              int(self.yDetectorSteps[em][det])))

                for b in bres:
                    if b[0] > -1 and b[0] < self.newImage.shape[1] and b[1] > -1 and b[1] < self.newImage.shape[0]:
                        self.newImage[b[1]][b[0]] += self.sinogram[em][det]
                        counter[b[1]][b[0]] += 1
                        if self.mainWindow.iterative:  # iterative display
                            iterativeImage[b[1]][b[0]] = self.newImage[b[1]][b[0]] / counter[b[1]][b[0]]

            if self.mainWindow.iterative:
                helper = toimage(iterativeImage)
                qout = ImageQt(helper)

                pixmap1 = QPixmap.fromImage(qout)
                pixmap1 = pixmap1.scaled(self.mainWindow.label_img_out.size(), Qt.KeepAspectRatio)

                self.mainWindow.label_img_out.setPixmap(pixmap1)

                self.mainWindow.app.processEvents()

        for row in range(0, len(self.newImage)):
            for col in range(0, len(self.newImage[row])):
                if counter[row][col] != 0:
                    self.newImage[row][col] /= counter[row][col]
                self.newImage[row][col] = self.newImage[row][col] ** 2

        self.newImage = np.interp(self.newImage, (np.min(self.newImage), np.max(self.newImage)),
                                  (0, 255))  # normalization of output image

    def filtering(self):

        for row in range(1, len(self.newImage) - 1):
            for col in range(1, len(self.newImage[row]) - 1):
                self.newImage[row][col] = (self.newImage[row][col] + self.newImage[row - 1][col - 1] +
                                           self.newImage[row - 1][col] + self.newImage[row + 1][col + 1] +
                                           self.newImage[row][col - 1] + self.newImage[row][col + 1] +
                                           self.newImage[row + 1][col - 1] + self.newImage[row + 1][col] +
                                           self.newImage[row + 1][col + 1]) / 9

    def rmse(self):
        sum = 0
        divider = 0
        for row in range(0, len(self.newImage)):
            for col in range(0, len(self.newImage[row])):
                sum += (self.image[row][col] - self.newImage[row][col]) ** 2
                divider += 1
        self.rmse = math.sqrt(sum / divider)
        print(self.rmse)
