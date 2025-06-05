import sys
from PyQt5.QtWidgets import QApplication
from .modules import DataCleanerUI, PlotterUI, FileCombinerUI, LiveViewerUI
from .widgets import SharedDataManager, LoadingSpinner
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magnet Data Analysis Tool")
        self.setGeometry(100, 100, 1400, 800)
        self.shared_data = SharedDataManager()

        # Setup assets
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        # Buttons
        btn_row = QHBoxLayout()
        layout.addLayout(btn_row)

        for name, ui in [("🧹 Cleaner", 0), ("📈 Plotter", 1), ("🔗 Combiner", 2), ("⚡ Live", 3)]:
            b = QPushButton(name)
            b.clicked.connect(lambda _, i=ui: self.stacked.setCurrentIndex(i))
            btn_row.addWidget(b)

        # Stacked views
        self.stacked = QStackedWidget()
        self.cleaner = DataCleanerUI(self.shared_data)
        self.plotter = PlotterUI(self.shared_data)
        self.combiner = FileCombinerUI(self.shared_data)
        self.live = LiveViewerUI()
        for w in [self.cleaner, self.plotter, self.combiner, self.live]:
            self.stacked.addWidget(w)

        layout.addWidget(self.stacked)


def run_app():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())