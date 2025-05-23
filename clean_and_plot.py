import sys
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QFileDialog, QListWidget,
                           QLabel, QComboBox, QStackedWidget, QRadioButton,
                           QButtonGroup, QGridLayout, QLineEdit, QSlider,
                           QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from scipy.signal import savgol_filter

class QRangeSlider(QWidget):
    valueChanged = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.min_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_slider = QSlider(Qt.Orientation.Horizontal)
        
        layout.addWidget(self.min_slider)
        layout.addWidget(self.max_slider)
        
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

class SharedDataManager:
    def __init__(self):
        self.cleaned_files = []

    def add_cleaned_file(self, file_path):
        if file_path not in self.cleaned_files:
            self.cleaned_files.append(file_path)

    def get_cleaned_files(self):
        return self.cleaned_files

class DataCleanerUI(QMainWindow):
    def __init__(self, shared_data_manager):
        super().__init__()
        self.shared_data_manager = shared_data_manager
        self.setWindowTitle("Data Cleaner")
        self.setGeometry(100, 100, 1400, 800)

        # Initialize data storage
        self.df = None
        self.selected_columns = []
        self.exclude_regions = []
        self.column_scales = {}

        # Create UI
        self.setup_ui()

    def update_scaling_controls(self):
        # Clear existing scaling controls
        for i in reversed(range(self.scaling_layout.count())):
            widget = self.scaling_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

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
            scale_combo.currentTextChanged.connect(
                lambda text, col=col_name: self.update_column_scale(col, text))
            scaling_layout.addWidget(scale_combo)

            self.scaling_layout.addWidget(scaling_group)

        self.update_plot()

    def update_column_scale(self, column, scale):
        self.column_scales[column] = scale
        self.update_plot()

    def setup_ui(self):
        # Main widget setup
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Left panel setup
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Add controls to left panel
        load_button = QPushButton("Load Data File")
        load_button.clicked.connect(self.load_file)
        left_layout.addWidget(load_button)

        # Column selection
        self.column_list = QListWidget()
        self.column_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.column_list.itemSelectionChanged.connect(self.update_scaling_controls)
        left_layout.addWidget(QLabel("Select Columns:"))
        left_layout.addWidget(self.column_list)

        # Scaling controls
        self.scaling_widget = QWidget()
        self.scaling_layout = QVBoxLayout(self.scaling_widget)
        left_layout.addWidget(QLabel("Column Scaling:"))
        left_layout.addWidget(self.scaling_widget)

        # Time range controls
        self.setup_time_controls(left_layout)

        # --- Exclude region time input controls ---
        self.exclude_start_input = QLineEdit()
        self.exclude_start_input.setPlaceholderText("Start")
        self.exclude_start_input.setFixedWidth(70)

        self.exclude_end_input = QLineEdit()
        self.exclude_end_input.setPlaceholderText("End")
        self.exclude_end_input.setFixedWidth(70)

        exclude_time_layout = QHBoxLayout()
        exclude_time_layout.addWidget(QLabel("Exclude Region:"))
        exclude_time_layout.addWidget(self.exclude_start_input)
        exclude_time_layout.addWidget(self.exclude_end_input)
        left_layout.addLayout(exclude_time_layout)

        # Add "Add Exclude Region" button
        exclude_button = QPushButton("Add Exclude Region")
        exclude_button.clicked.connect(self.add_exclude_region)
        left_layout.addWidget(exclude_button)

        # Exclude region list and remove button
        self.exclude_list = QListWidget()
        left_layout.addWidget(QLabel("Excluded Regions:"))
        left_layout.addWidget(self.exclude_list)
        remove_region_button = QPushButton("Remove Selected Region")
        remove_region_button.clicked.connect(self.remove_exclude_region)
        left_layout.addWidget(remove_region_button)

        # Save button
        save_button = QPushButton("Save Cleaned Data")
        save_button.clicked.connect(self.save_data)
        left_layout.addWidget(save_button)

        # Right panel setup
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)

        # Add panels to main layout
        layout.addWidget(left_panel, stretch=1)
        layout.addWidget(right_panel, stretch=2)

    def remove_exclude_region(self):
        selected_items = self.exclude_list.selectedItems()
        for item in selected_items:
            row = self.exclude_list.row(item)
            self.exclude_list.takeItem(row)
            del self.exclude_regions[row]
        self.update_plot()

    def add_exclude_region(self):
        try:
            if self.exclude_start_input.text() and self.exclude_end_input.text():
                start = float(self.exclude_start_input.text())
                end = float(self.exclude_end_input.text())
            else:
                start, end = self.time_slider.value()

            if start > end:
                start, end = end, start

            self.exclude_regions.append((start, end))
            self.exclude_list.addItem(f"{start:.1f} - {end:.1f}")
            self.update_plot()
        except ValueError:
            pass

    def setup_time_controls(self, parent_layout):
        time_control_widget = QWidget()
        time_control_layout = QHBoxLayout(time_control_widget)
        
        self.min_time_input = QLineEdit()
        self.max_time_input = QLineEdit()
        self.min_time_input.setFixedWidth(70)
        self.max_time_input.setFixedWidth(70)
        
        self.time_slider = QRangeSlider()
        
        time_control_layout.addWidget(QLabel("Min:"))
        time_control_layout.addWidget(self.min_time_input)
        time_control_layout.addWidget(QLabel("Max:"))
        time_control_layout.addWidget(self.max_time_input)
        
        parent_layout.addWidget(QLabel("Time Range:"))
        parent_layout.addWidget(self.time_slider)
        parent_layout.addWidget(time_control_widget)

        # Connect signals
        self.min_time_input.returnPressed.connect(self.update_time_from_input)
        self.max_time_input.returnPressed.connect(self.update_time_from_input)
        self.time_slider.valueChanged.connect(self.update_time_display)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Data File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            try:
                # Read the CSV file with custom logic for multi-level columns
                self.df = pd.read_csv(file_path, delimiter=';', skiprows=1, header=[0, 1])
                self.df = self.df.dropna(axis=1, how='all')
                self.df.columns = [self._flatten_col(col) for col in self.df.columns]
                self.df = self.df.apply(pd.to_numeric, errors='coerce')
                if 'Timestamp' in self.df.columns:
                    self.df['Timestamp'] = self.df['Timestamp'] / 1000 / 60
                # Update the column list
                self.column_list.clear()
                self.column_list.addItems(self.df.columns)
                # If there's a timestamp column, set up the time range
                if 'Timestamp' in self.df.columns:
                    min_time = int(self.df['Timestamp'].min())
                    max_time = int(self.df['Timestamp'].max())
                    self.time_slider.setRange(min_time, max_time)
                    self.min_time_input.setText(f"{min_time:.1f}")
                    self.max_time_input.setText(f"{max_time:.1f}")
                # Update the plot
                self.update_plot()
                # Add the file to shared data manager
                self.shared_data_manager.add_cleaned_file(file_path)
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

    def update_plot(self):
        if self.df is None:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Get selected columns
        selected_items = self.column_list.selectedItems()
        selected_columns = [item.text() for item in selected_items]

        # Filter by time range if possible
        df_filtered = self.df
        if 'Timestamp' in self.df.columns:
            try:
                time_range = self.time_slider.value()
                mask = (self.df['Timestamp'] >= time_range[0]) & (self.df['Timestamp'] <= time_range[1])
                df_filtered = self.df[mask]
            except Exception:
                pass
            # Apply exclude regions
            for region in self.exclude_regions:
                mask = ~((df_filtered['Timestamp'] >= region[0]) & (df_filtered['Timestamp'] <= region[1]))
                df_filtered = df_filtered[mask]

        # Plot selected columns
        for col in selected_columns:
            if col in df_filtered.columns:
                # Get scale text and factor
                scale_text = self.column_scales.get(col, '1x')
                scale_factor = {
                    '÷10': 0.1,
                    '÷100': 0.01,
                    '÷1000': 0.001
                }.get(scale_text, 1.0)
                y_data = df_filtered[col] * scale_factor
                if 'Timestamp' in df_filtered.columns:
                    ax.plot(df_filtered['Timestamp'], y_data, label=f"{col} ({scale_text})")
                else:
                    ax.plot(df_filtered.index, y_data, label=f"{col} ({scale_text})")

        if 'Timestamp' in df_filtered.columns:
            ax.set_xlabel('Timestamp')
        else:
            ax.set_xlabel('Index')
        ax.set_ylabel('Value')
        ax.grid(True)
        ax.legend()
        self.canvas.draw()

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
        """Update the time input displays when the slider changes"""
        self.min_time_input.setText(f"{values[0]:.1f}")
        self.max_time_input.setText(f"{values[1]:.1f}")
        self.update_plot()

    def save_data(self):
        if self.df is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Cleaned Data", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            # Apply time range filter
            time_range = self.time_slider.value()
            mask = (self.df['Timestamp'] >= time_range[0]) & \
                   (self.df['Timestamp'] <= time_range[1])
            df_filtered = self.df[mask].copy()

            # Apply exclude regions
            for region in self.exclude_regions:
                mask = ~((df_filtered['Timestamp'] >= region[0]) & (df_filtered['Timestamp'] <= region[1]))
                df_filtered = df_filtered[mask]

            # Apply scaling
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

            # Save the filtered and scaled data
            df_filtered.to_csv(file_path, index=False)

            # Add the saved file to shared data manager
            self.shared_data_manager.add_cleaned_file(file_path)

    # Add the rest of the DataCleanerUI methods here...
    # (update_plot, etc.)

class PlotterUI(QMainWindow):
    def __init__(self, shared_data_manager):
        super().__init__()
        self.shared_data_manager = shared_data_manager
        self.setWindowTitle("IV Plotter")
        self.setGeometry(100, 100, 1400, 800)

        self.df = None
        self.setup_ui()

    def setup_ui(self):
        # Setup the main UI components
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Left panel setup
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # File selection
        self.setup_file_selection(left_layout)

        # Axis controls
        self.setup_axis_controls(left_layout)

        # Plot controls
        self.setup_plot_controls(left_layout)

        # Right panel with plot
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.setup_plot_area(right_layout)

        # Add panels to main layout
        layout.addWidget(left_panel, stretch=1)
        layout.addWidget(right_panel, stretch=2)

    def setup_file_selection(self, layout):
        self.load_button = QPushButton("Load Cleaned File")
        self.load_button.clicked.connect(self.load_file)
        layout.addWidget(self.load_button)
        self.file_list = QListWidget()
        layout.addWidget(QLabel("Available Files:"))
        layout.addWidget(self.file_list)

    def setup_axis_controls(self, layout):
        self.x_axis_combo = QComboBox()
        self.y1_axis_combo = QComboBox()
        self.y2_axis_combo = QComboBox()
        self.y2_axis_combo.setEnabled(False)

        self.x_label_input = QLineEdit()
        self.x_label_input.setPlaceholderText("X-axis Label")

        self.y1_label_input = QLineEdit()
        self.y1_label_input.setPlaceholderText("Left Y-axis Label")

        self.y2_label_input = QLineEdit()
        self.y2_label_input.setPlaceholderText("Right Y-axis Label")
        self.y2_label_input.setEnabled(False)

        self.enable_y2_checkbox = QCheckBox("Enable Second Y-axis")
        self.enable_y2_checkbox.stateChanged.connect(self.toggle_second_y_axis)

        self.x_min_input = QLineEdit()
        self.x_max_input = QLineEdit()
        self.x_min_input.setFixedWidth(70)
        self.x_max_input.setFixedWidth(70)
        self.x_min_input.setPlaceholderText("X min")
        self.x_max_input.setPlaceholderText("X max")

        # Add absolute value checkboxes for Y1 and Y2
        self.y1_abs_checkbox = QCheckBox("Use |Y1|")
        self.y2_abs_checkbox = QCheckBox("Use |Y2|")
        self.y2_abs_checkbox.setEnabled(False)

        layout.addWidget(QLabel("X Axis:"))
        layout.addWidget(self.x_axis_combo)
        layout.addWidget(self.x_label_input)
        layout.addWidget(QLabel("Y1 Axis:"))
        layout.addWidget(self.y1_axis_combo)
        layout.addWidget(self.y1_label_input)
        layout.addWidget(self.y1_abs_checkbox)
        layout.addWidget(self.enable_y2_checkbox)
        layout.addWidget(QLabel("Y2 Axis:"))
        layout.addWidget(self.y2_axis_combo)
        layout.addWidget(self.y2_label_input)
        layout.addWidget(self.y2_abs_checkbox)
        layout.addWidget(QLabel("X range:"))
        layout.addWidget(self.x_min_input)
        layout.addWidget(self.x_max_input)

    def toggle_second_y_axis(self, state):
        enabled = state == Qt.Checked
        self.y2_axis_combo.setEnabled(enabled)
        self.y2_label_input.setEnabled(enabled)
        self.y2_abs_checkbox.setEnabled(enabled)

    def setup_plot_controls(self, layout):
        plot_button = QPushButton("Plot")
        plot_button.clicked.connect(self.plot_selected)
        layout.addWidget(plot_button)

    def setup_plot_area(self, layout):
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def update_file_list(self):
        self.file_list.clear()
        for f in self.shared_data_manager.get_cleaned_files():
            self.file_list.addItem(f)

    def load_file(self):
        if self.file_list.currentItem():
            file_path = self.file_list.currentItem().text()
            try:
                self.df = pd.read_csv(file_path)
                self.x_axis_combo.clear()
                self.y1_axis_combo.clear()
                self.y2_axis_combo.clear()
                self.x_axis_combo.addItems(self.df.columns)
                self.y1_axis_combo.addItems(self.df.columns)
                self.y2_axis_combo.addItems(self.df.columns)
            except Exception as e:
                print(f"Failed to load file: {e}")

    def plot_selected(self):
        if self.df is not None:
            x_col = self.x_axis_combo.currentText()
            y1_col = self.y1_axis_combo.currentText()
            y2_col = self.y2_axis_combo.currentText() if self.y2_axis_combo.isEnabled() else None
            x_min = float(self.x_min_input.text()) if self.x_min_input.text() else None
            x_max = float(self.x_max_input.text()) if self.x_max_input.text() else None

            self.figure.clear()
            ax1 = self.figure.add_subplot(111)
            ax2 = ax1.twinx() if y2_col else None

            x_data = self.df[x_col]

            mask = pd.Series(True, index=self.df.index)
            if x_min is not None:
                mask &= x_data >= x_min
            if x_max is not None:
                mask &= x_data <= x_max

            x_data = x_data[mask]

            if y1_col:
                y1_data = self.df[y1_col][mask]
                if self.y1_abs_checkbox.isChecked():
                    y1_data = y1_data.abs()
                ax1.plot(x_data, y1_data, label=y1_col, color='tab:blue')
                ax1.set_ylabel(self.y1_label_input.text() or y1_col, color='tab:blue')
                ax1.tick_params(axis='y', labelcolor='tab:blue')

            if y2_col:
                y2_data = self.df[y2_col][mask]
                if self.y2_abs_checkbox.isChecked():
                    y2_data = y2_data.abs()
                ax2.plot(x_data, y2_data, label=y2_col, color='tab:red')
                ax2.set_ylabel(self.y2_label_input.text() or y2_col, color='tab:red')
                ax2.tick_params(axis='y', labelcolor='tab:red')

            # Set X-axis label using input
            ax1.set_xlabel(self.x_label_input.text() or x_col)
            ax1.grid(True)

            # Add combined legend at bottom right
            lines, labels = ax1.get_legend_handles_labels()
            if ax2:
                l2, lb2 = ax2.get_legend_handles_labels()
                lines += l2
                labels += lb2
            ax1.legend(lines, labels, loc='lower right')

            self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Analysis Tool")
        self.setGeometry(100, 100, 1400, 800)

        self.shared_data_manager = SharedDataManager()
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Mode selection buttons
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        
        cleaner_button = QPushButton("Data Cleaner")
        plotter_button = QPushButton("IV Plotter")
        
        button_layout.addWidget(cleaner_button)
        button_layout.addWidget(plotter_button)
        layout.addWidget(button_widget)

        # Stacked widget for interfaces
        self.stacked_widget = QStackedWidget()
        self.cleaner = DataCleanerUI(self.shared_data_manager)
        self.plotter = PlotterUI(self.shared_data_manager)
        
        self.stacked_widget.addWidget(self.cleaner)
        self.stacked_widget.addWidget(self.plotter)
        
        layout.addWidget(self.stacked_widget)

        # Connect buttons
        cleaner_button.clicked.connect(self.switch_to_cleaner)
        plotter_button.clicked.connect(self.switch_to_plotter)

    def switch_to_cleaner(self):
        self.stacked_widget.setCurrentIndex(0)

    def switch_to_plotter(self):
        self.stacked_widget.setCurrentIndex(1)
        self.plotter.update_file_list()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())