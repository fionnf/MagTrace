import sys
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QListWidget,
                             QLabel, QSlider, QCheckBox, QComboBox, QGridLayout,
                             QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from scipy.signal import savgol_filter


class DataCleanerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Cleaner")
        self.setGeometry(100, 100, 1400, 800)

        # Initialize data storage
        self.df = None
        self.selected_columns = []
        self.exclude_regions = []
        self.column_scales = {}  # Store scaling factors for columns

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
        self.column_list.itemSelectionChanged.connect(self.update_scaling_controls)
        left_layout.addWidget(QLabel("Select Columns:"))
        left_layout.addWidget(self.column_list)

        # Add scaling controls container
        self.scaling_widget = QWidget()
        self.scaling_layout = QVBoxLayout(self.scaling_widget)
        left_layout.addWidget(QLabel("Column Scaling:"))
        left_layout.addWidget(self.scaling_widget)

        # Add time range controls
        time_control_widget = QWidget()
        time_control_layout = QHBoxLayout(time_control_widget)
        
        # Min time input
        self.min_time_input = QLineEdit()
        self.min_time_input.setFixedWidth(70)
        self.min_time_input.returnPressed.connect(self.update_time_from_input)
        
        # Max time input
        self.max_time_input = QLineEdit()
        self.max_time_input.setFixedWidth(70)
        self.max_time_input.returnPressed.connect(self.update_time_from_input)
        
        # Add time range slider
        self.time_slider = QRangeSlider()
        self.time_slider.valueChanged.connect(self.update_time_display)
        
        time_control_layout.addWidget(QLabel("Min:"))
        time_control_layout.addWidget(self.min_time_input)
        time_control_layout.addWidget(QLabel("Max:"))
        time_control_layout.addWidget(self.max_time_input)
        
        left_layout.addWidget(QLabel("Time Range:"))
        left_layout.addWidget(self.time_slider)
        left_layout.addWidget(time_control_widget)

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

        # Add matplotlib figure and toolbar
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)

        # Add panels to main layout
        layout.addWidget(left_panel, stretch=1)
        layout.addWidget(right_panel, stretch=2)

    # Add these new methods to handle time range inputs:
    def update_time_from_input(self):
        try:
            min_time = float(self.min_time_input.text())
            max_time = float(self.max_time_input.text())
            
            if min_time > max_time:
                min_time, max_time = max_time, min_time
                
            slider_min = self.time_slider.min_slider.minimum()
            slider_max = self.time_slider.max_slider.maximum()
            
            # Ensure values are within slider range
            min_time = max(slider_min, min(slider_max, min_time))
            max_time = max(slider_min, min(slider_max, max_time))
            
            self.time_slider.setValue((int(min_time), int(max_time)))
            self.update_plot()
        except ValueError:
            # Restore previous values if input is invalid
            self.update_time_display(self.time_slider.value())

    def update_time_display(self, values):
        self.min_time_input.setText(f"{values[0]:.1f}")
        self.max_time_input.setText(f"{values[1]:.1f}")
        self.update_plot()

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Data File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            try:
                # Read the CSV file with semicolon delimiter and skip first row
                self.df = pd.read_csv(file_path, delimiter=';', skiprows=1, header=[0, 1])
                self.df = self.df.dropna(axis=1, how='all')
                
                # Flatten column headers
                self.df.columns = [self._flatten_col(col) for col in self.df.columns]
                
                # Convert to numeric and handle timestamps
                self.df = self.df.apply(pd.to_numeric, errors='coerce')
                if 'Timestamp' in self.df.columns:
                    self.df['Timestamp'] = self.df['Timestamp'] / 1000 / 60  # Convert to minutes
                
                # Update the column list
                self.column_list.clear()
                self.column_list.addItems(self.df.columns)
                
                # Set the time range slider and inputs
                if 'Timestamp' in self.df.columns:
                    min_time = int(self.df['Timestamp'].min())
                    max_time = int(self.df['Timestamp'].max())
                    self.time_slider.setRange(min_time, max_time)
                    self.min_time_input.setText(f"{min_time:.1f}")
                    self.max_time_input.setText(f"{max_time:.1f}")
                
                # Clear existing exclude regions and scales
                self.exclude_regions.clear()
                self.exclude_list.clear()
                self.column_scales.clear()
                
                # Update the plot
                self.update_plot()
                
            except Exception as e:
                print(f"Error loading file: {str(e)}")

    def _flatten_col(self, col):
        if isinstance(col, tuple):
            first = str(col[0]).strip() if pd.notna(col[0]) else ""
            second = str(col[1]).strip() if pd.notna(col[1]) else ""
            if second and second != first:
                return f"{first}({second})"
            return first
        return str(col).strip()

    def update_scaling_controls(self):
        # Clear existing scaling controls
        for i in reversed(range(self.scaling_layout.count())):
            self.scaling_layout.itemAt(i).widget().setParent(None)

        # Add scaling controls for selected columns
        selected_items = self.column_list.selectedItems()
        for item in selected_items:
            col_name = item.text()
            scaling_group = QWidget()
            scaling_layout = QHBoxLayout(scaling_group)

            # Add column label
            scaling_layout.addWidget(QLabel(col_name))

            # Add scaling combo box
            scale_combo = QComboBox()
            scale_combo.addItems(['1x', '÷10', '÷100', '÷1000'])
            scale_combo.setCurrentText(self.column_scales.get(col_name, '1x'))
            scale_combo.currentTextChanged.connect(lambda text, col=col_name: self.update_column_scale(col, text))
            scaling_layout.addWidget(scale_combo)

            self.scaling_layout.addWidget(scaling_group)

        self.update_plot()

    def update_column_scale(self, column, scale):
        self.column_scales[column] = scale
        self.update_plot()

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

        # Plot selected columns with scaling
        for col in selected_columns:
            scale_text = self.column_scales.get(col, '1x')
            scale_factor = 1.0
            if scale_text == '÷10':
                scale_factor = 0.1
            elif scale_text == '÷100':
                scale_factor = 0.01
            elif scale_text == '÷1000':
                scale_factor = 0.001

            ax.plot(df_filtered['Timestamp'],
                    df_filtered[col] * scale_factor,
                    label=f"{col} ({scale_text})")

        ax.set_xlabel('Time (minutes)')
        ax.set_ylabel('Value')
        ax.grid(True)
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
            
            # Apply scaling and update column names
            for column, scale in self.column_scales.items():
                if scale != '1x' and column in df_filtered.columns:
                    scale_factor = {
                        '÷10': 0.1,
                        '÷100': 0.01,
                        '÷1000': 0.001
                    }.get(scale, 1.0)
                    
                    # Apply scaling to the data
                    df_filtered[column] = df_filtered[column] * scale_factor
                    
                    # Update column name to reflect scaling
                    new_column = f"{column}_{scale[1:]}"  # Remove the '÷' symbol
                    df_filtered.rename(columns={column: new_column}, inplace=True)
            
            df_filtered.to_csv(file_path, index=False)


class QRangeSlider(QWidget):
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
        self.valueChanged.emit(self.value())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataCleanerUI()
    window.show()
    sys.exit(app.exec())