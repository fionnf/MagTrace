# modules.py

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QComboBox, QLineEdit, QCheckBox, QListWidget, QFileDialog)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
from .widgets import QRangeSlider
from .utils import flatten_col


# --- Data Cleaner ---
class DataCleanerUI(QMainWindow):
    def __init__(self, shared_data_manager):
        super().__init__()
        self.setWindowTitle("Data Cleaner")
        self.shared_data_manager = shared_data_manager
        self.df = None
        self.exclude_regions = []

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Left side
        self.column_list = QListWidget()
        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load_file)
        self.exclude_start_input = QLineEdit()
        self.exclude_end_input = QLineEdit()
        self.exclude_button = QPushButton("Add Exclude")
        self.exclude_button.clicked.connect(self.add_exclude)
        self.exclude_list = QListWidget()

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.load_button)
        left_layout.addWidget(QLabel("Columns:"))
        left_layout.addWidget(self.column_list)
        left_layout.addWidget(QLabel("Exclude Start:"))
        left_layout.addWidget(self.exclude_start_input)
        left_layout.addWidget(QLabel("Exclude End:"))
        left_layout.addWidget(self.exclude_end_input)
        left_layout.addWidget(self.exclude_button)
        left_layout.addWidget(QLabel("Excluded regions:"))
        left_layout.addWidget(self.exclude_list)

        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        # Right side
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)

        right_panel = QWidget()
        right_panel.setLayout(right_layout)

        layout.addWidget(left_panel)
        layout.addWidget(right_panel)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            self.df = pd.read_csv(path, delimiter=';', skiprows=1, header=[0, 1])
            self.df.columns = [flatten_col(col) for col in self.df.columns]
            self.column_list.clear()
            self.column_list.addItems(self.df.columns)
            self.shared_data_manager.add_cleaned_file(path)
            self.plot()

    def add_exclude(self):
        try:
            start = float(self.exclude_start_input.text())
            end = float(self.exclude_end_input.text())
            self.exclude_regions.append((start, end))
            self.exclude_list.addItem(f"{start} - {end}")
            self.plot()
        except ValueError:
            pass

    def plot(self):
        if self.df is None or 'Timestamp' not in self.df.columns:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        df_filtered = self.df.copy()
        for start, end in self.exclude_regions:
            df_filtered = df_filtered[~((df_filtered['Timestamp'] >= start) & (df_filtered['Timestamp'] <= end))]
        for col in self.df.columns:
            if col != 'Timestamp':
                ax.plot(df_filtered['Timestamp'], df_filtered[col], label=col)
        ax.set_xlabel("Timestamp")
        ax.legend()
        ax.grid(True)
        self.canvas.draw()


# --- Plotter ---
class PlotterUI(QMainWindow):
    def __init__(self, shared_data_manager):
        super().__init__()
        self.setWindowTitle("Plotter")
        self.shared_data_manager = shared_data_manager
        self.df = None
        self.y2_combo = QComboBox()
        self.y3_combo = QComboBox()
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        self.file_list = QListWidget()
        self.file_list.addItems(self.shared_data_manager.get_cleaned_files())
        self.file_list.itemClicked.connect(self.load_file)

        self.x_combo = QComboBox()
        self.y_combo = QComboBox()

        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self.plot)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.file_list)
        layout.addWidget(QLabel("X axis:"))
        layout.addWidget(self.x_combo)
        layout.addWidget(QLabel("Y axis:"))
        layout.addWidget(self.y_combo)
        layout.addWidget(QLabel("Y2 axis:"))
        layout.addWidget(self.y2_combo)
        layout.addWidget(QLabel("Y3 axis:"))
        layout.addWidget(self.y3_combo)
        layout.addWidget(self.plot_button)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def load_file(self):
        path = self.file_list.currentItem().text()
        self.df = pd.read_csv(path)
        self.x_combo.clear()
        self.y_combo.clear()
        self.y2_combo.clear()
        self.y3_combo.clear()
        self.x_combo.addItems(self.df.columns)
        self.y_combo.addItems(self.df.columns)
        self.y2_combo.addItems(self.df.columns)
        self.y3_combo.addItems(self.df.columns)

    def plot(self):
        if self.df is not None:
            x = self.x_combo.currentText()
            y = self.y_combo.currentText()
            y2 = self.y2_combo.currentText()
            y3 = self.y3_combo.currentText()

            self.figure.clear()
            ax1 = self.figure.add_subplot(111)
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()

            ax3.spines["right"].set_position(("outward", 60))
            ax3.spines["right"].set_visible(True)

            ax1.plot(self.df[x], self.df[y], color='tab:blue', label=y)
            ax2.plot(self.df[x], self.df[y2], color='tab:orange', label=y2)
            ax3.plot(self.df[x], self.df[y3], color='tab:green', label=y3)

            ax1.set_xlabel(x)
            ax1.set_ylabel(y, color='tab:blue')
            ax2.set_ylabel(y2, color='tab:orange')
            ax3.set_ylabel(y3, color='tab:green')

            ax1.tick_params(axis='y', labelcolor='tab:blue')
            ax2.tick_params(axis='y', labelcolor='tab:orange')
            ax3.tick_params(axis='y', labelcolor='tab:green')

            ax1.grid(True)
            self.canvas.draw()


# --- File Combiner ---
class FileCombinerUI(QMainWindow):
    def __init__(self, shared_data_manager):
        super().__init__()
        self.setWindowTitle("File Combiner")
        self.shared_data_manager = shared_data_manager
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        self.file_list.addItems(self.shared_data_manager.get_cleaned_files())

        self.combine_button = QPushButton("Combine")
        self.combine_button.clicked.connect(self.combine_files)

        layout.addWidget(QLabel("Select files to combine:"))
        layout.addWidget(self.file_list)
        layout.addWidget(self.combine_button)

    def combine_files(self):
        selected = self.file_list.selectedItems()
        paths = [item.text() for item in selected]
        dfs = []
        offset = 0
        for path in paths:
            df = pd.read_csv(path)
            if 'Timestamp' in df.columns:
                df['Timestamp'] += offset
                offset = df['Timestamp'].iloc[-1] + 0.01
            dfs.append(df)
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            path, _ = QFileDialog.getSaveFileName(self, "Save Combined", "", "CSV Files (*.csv)")
            if path:
                combined.to_csv(path, index=False)
                self.shared_data_manager.add_cleaned_file(path)


# --- Live Viewer (Placeholder) ---
class LiveViewerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Viewer")
        label = QLabel("Live data visualization UI coming soon.")
        layout = QVBoxLayout()
        layout.addWidget(label)
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)