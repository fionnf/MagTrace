from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMovie


class QRangeSlider(QWidget):
    valueChanged = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.min_slider = QSlider(Qt.Horizontal)
        self.max_slider = QSlider(Qt.Horizontal)
        layout.addWidget(self.min_slider)
        layout.addWidget(self.max_slider)

        self.min_slider.valueChanged.connect(self.update_range)
        self.max_slider.valueChanged.connect(self.update_range)

    def setRange(self, min_, max_):
        self.min_slider.setRange(min_, max_)
        self.max_slider.setRange(min_, max_)
        self.max_slider.setValue(max_)

    def setValue(self, value):
        self.min_slider.setValue(value[0])
        self.max_slider.setValue(value[1])

    def value(self):
        return (self.min_slider.value(), self.max_slider.value())

    def update_range(self):
        if self.min_slider.value() > self.max_slider.value():
            self.min_slider.setValue(self.max_slider.value())
        self.valueChanged.emit(self.value())


class SharedDataManager:
    def __init__(self):
        self.cleaned_files = []

    def add_cleaned_file(self, path):
        if path not in self.cleaned_files:
            self.cleaned_files.append(path)

    def get_cleaned_files(self):
        return self.cleaned_files

class LoadingSpinner(QLabel):
    def __init__(self, gif_path="assets/spinning_magnet.gif"):
        super().__init__()
        self.movie = QMovie(gif_path)
        self.setMovie(self.movie)
        self.setVisible(False)

    def start(self):
        self.setVisible(True)
        self.movie.start()

    def stop(self):
        self.movie.stop()
        self.setVisible(False)