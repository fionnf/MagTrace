import sys
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QFileDialog, QListWidget, 
                           QLabel, QSlider, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.signal import savgol_filter

class DataCleanerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Cleaner")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize data storage
        self.df = None
        self.selected_columns = []
        self.exclude_regions = []
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Add file loading button
        load_button = QPushButton("Load Data File")
        load_button.clicked.connect(self.load_file)
        left_layout.addWidget(load_button)
        
        # Add column selection list
        self.column_list = QListWidget()
        self.column_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.column_list.itemSelectionChanged.connect(self.update_plot)
        left_layout.addWidget(QLabel("Select Columns:"))
        left_layout.addWidget(self.column_list)
        
        # Add time range slider
        self.time_slider = QRangeSlider()
        left_layout.addWidget(QLabel("Time Range:"))
        left_layout.addWidget(self.time_slider)
        self.time_slider.valueChanged.connect(self.update_plot)
        
        # Add exclude region controls
        exclude_button = QPushButton("Add Exclude Region")
        exclude_button.clicked.connect(self.add_exclude_region)
        left_layout.addWidget(exclude_button)
        
        # Add exclude regions list
        self.exclude_list = QListWidget()
        left_layout.addWidget(QLabel("Excluded Regions:"))
        left_layout.addWidget(self.exclude_list)
        
        # Add save button
        save_button = QPushButton("Save Cleaned Data")
        save_button.clicked.connect(self.save_data)
        left_layout.addWidget(save_button)
        
        # Create right panel for plot
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Add matplotlib figure
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        
        # Add panels to main layout
        layout.addWidget(left_panel, stretch=1)
        layout.addWidget(right_panel, stretch=2)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.df = self.load_and_process_file(file_path)
            self.update_column_list()
            self.setup_time_slider()
            self.update_plot()

    def load_and_process_file(self, file_path):
        try:
            df = pd.read_csv(file_path, delimiter=';', skiprows=1, header=[0, 1])
            df = df.dropna(axis=1, how='all')
            df.columns = [self.flatten_col(col) for col in df.columns]
            df = df.apply(pd.to_numeric, errors='coerce')
            df['Timestamp'] = df['Timestamp'] / (1000 * 60)  # Convert to minutes
            return df
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            return None

    @staticmethod
    def flatten_col(col):
        if isinstance(col, tuple):
            first = str(col[0]).strip() if pd.notna(col[0]) else ""
            second = str(col[1]).strip() if pd.notna(col[1]) else ""
            return f"{first}({second})" if second and second != first else first
        return str(col).strip()

    def update_column_list(self):
        self.column_list.clear()
        if self.df is not None:
            self.column_list.addItems(self.df.columns)

    def setup_time_slider(self):
        if self.df is not None:
            min_time = self.df['Timestamp'].min()
            max_time = self.df['Timestamp'].max()
            self.time_slider.setRange(min_time, max_time)
            self.time_slider.setValue((min_time, max_time))

    def update_plot(self):
        if self.df is None:
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Get selected columns and time range
        selected_items = self.column_list.selectedItems()
        selected_columns = [item.text() for item in selected_items]
        time_range = self.time_slider.value()
        
        # Filter data by time range
        mask = (self.df['Timestamp'] >= time_range[0]) & \
               (self.df['Timestamp'] <= time_range[1])
        df_filtered = self.df[mask].copy()
        
        # Apply exclude regions
        for region in self.exclude_regions:
            mask = ~((df_filtered['Timestamp'] >= region[0]) & \
                    (df_filtered['Timestamp'] <= region[1]))
            df_filtered = df_filtered[mask]
        
        # Plot selected columns
        for col in selected_columns:
            ax.plot(df_filtered['Timestamp'], df_filtered[col], label=col)
            
        ax.set_xlabel('Time (minutes)')
        ax.set_ylabel('Value')
        ax.legend()
        self.canvas.draw()

    def add_exclude_region(self):
        # Get current time range selection
        time_range = self.time_slider.value()
        self.exclude_regions.append(time_range)
        self.exclude_list.addItem(f"{time_range[0]:.1f} - {time_range[1]:.1f}")
        self.update_plot()

    def save_data(self):
        if self.df is None:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Cleaned Data", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            # Apply all filters and save
            time_range = self.time_slider.value()
            mask = (self.df['Timestamp'] >= time_range[0]) & \
                   (self.df['Timestamp'] <= time_range[1])
            df_filtered = self.df[mask].copy()
            
            for region in self.exclude_regions:
                mask = ~((df_filtered['Timestamp'] >= region[0]) & \
                        (df_filtered['Timestamp'] <= region[1]))
                df_filtered = df_filtered[mask]
            
            df_filtered.to_csv(file_path, index=False)

class QRangeSlider(QWidget):
    # Define the valueChanged signal
    valueChanged = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Create two sliders
        self.min_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_slider = QSlider(Qt.Orientation.Horizontal)
        
        layout.addWidget(self.min_slider)
        layout.addWidget(self.max_slider)
        
        # Connect signals
        self.min_slider.valueChanged.connect(self.update_range)
        self.max_slider.valueChanged.connect(self.update_range)

    def setRange(self, minimum, maximum):
        self.min_slider.setRange(minimum, maximum)
        self.max_slider.setRange(minimum, maximum)
        self.max_slider.setValue(maximum)

    def value(self):
        return (self.min_slider.value(), self.max_slider.value())

    def setValue(self, value):
        self.min_slider.setValue(value[0])
        self.max_slider.setValue(value[1])

    def update_range(self):
        if self.min_slider.value() > self.max_slider.value():
            self.min_slider.setValue(self.max_slider.value())
        # Emit the valueChanged signal with the current values
        self.valueChanged.emit(self.value())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataCleanerUI()
    window.show()
    sys.exit(app.exec())