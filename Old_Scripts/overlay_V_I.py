import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
from scipy.signal import savgol_filter

# Define the function to flatten header columns
def flatten_col(col):
    if isinstance(col, tuple):
        first = str(col[0]).strip() if pd.notna(col[0]) else ""
        second = str(col[1]).strip() if pd.notna(col[1]) else ""
        if second and second != first:
            return f"{first}({second})"
        else:
            return first
    else:
        return str(col).strip()

# Define the function to load and process the file
def load_and_process_file(file_path):
    df = pd.read_csv(file_path)
    df.columns = [flatten_col(col) for col in df.columns]
    df = df.apply(pd.to_numeric, errors='coerce')
    return df

# Define the function to find the cleaned CSV file in a folder
def find_cleaned_csv(folder_path):
    for file_name in os.listdir(folder_path):
        if 'clean' in file_name:
            return os.path.join(folder_path, file_name)
    return None

# Define the function to apply a Savitzky-Golay filter
def savitzky_golay_filter(data, window_size, polyorder):
    return savgol_filter(data, window_size, polyorder)

# Define the function to overlay plots from multiple folders with custom labels
def overlay_plots(base_path, folder_labels, hall_sensor_col, current_col, voltage_col_1, voltage_col_2, voltage_divide_1, voltage_divide_2, plot_title):
    plt.rcParams.update({
        'axes.edgecolor': 'black',
        'axes.linewidth': 1.5,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.major.size': 5,
        'ytick.major.size': 5,
        'xtick.minor.size': 3,
        'ytick.minor.size': 3,
        'xtick.major.width': 1.5,
        'ytick.major.width': 1.5,
        'xtick.minor.width': 1.0,
        'ytick.minor.width': 1.0,
        'axes.grid': True,
        'grid.alpha': 0.5,
        'grid.linestyle': '',
        'font.serif': 'Arial',
        'font.size': 18,
        'axes.titlesize': 18,
        'axes.labelsize': 18,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'legend.fontsize': 18,
    })

    fig, ax1 = plt.subplots(figsize=(10, 7))
    ax2 = ax1.twinx()

    for folder, label in folder_labels.items():
        folder_path = os.path.join(base_path, folder)
        cleaned_csv_path = find_cleaned_csv(folder_path)

        if cleaned_csv_path:
            df = load_and_process_file(cleaned_csv_path)
            voltage_column = voltage_col_1 if folder == list(folder_labels.keys())[0] else voltage_col_2
            voltage_divisor = voltage_divide_1 if folder == list(folder_labels.keys())[0] else voltage_divide_2
            voltage_filtered = savgol_filter(abs(df[voltage_column]) / voltage_divisor, window_length=700, polyorder=2)
            ax1.scatter(df[current_col], abs(df[hall_sensor_col]), label=f'{label}', color='tab:blue', s=15)
            ax2.scatter(df[current_col], voltage_filtered, label=f'', color='tab:red', s=5)
        else:
            print(f"No cleaned CSV file found in folder: {folder}")

    for i, (folder, label) in enumerate(folder_labels.items()):
        magnetic_color = colors[f'set{i + 1}']['field']
        voltage_color = colors[f'set{i + 1}']['voltage']

        ax1.scatter(df[current_col], abs(df[hall_sensor_col]), label=f'{label} Magnetic', color=magnetic_color, s=15)
        ax2.scatter(df[current_col], voltage_filtered, label=f'{label} Voltage', color=voltage_color, s=5, marker='x')

    ax1.set_xlabel('Current (A)')
    ax1.set_ylabel('Magnetic Field (T)')
    ax2.set_ylabel('Potential (mV)')
    ax1.tick_params(axis='y')
    ax2.tick_params(axis='y')
    ax1.tick_params(top=True, labeltop=False)  # Place ticks on top
    ax2.tick_params(top=True, labeltop=False)  # Place ticks on top
    ax1.minorticks_on()  # Enable minor ticks
    ax2.minorticks_on()  # Enable minor ticks
    #ax1.legend()
    ax1.tick_params(which='minor', top=True)  # Minor ticks on top
    ax2.tick_params(which='minor', top=True)  # Minor ticks on top
    fig.suptitle(plot_title)

    date_str = datetime.now().strftime('%d%m%Y')
    plt.savefig(f'Plots/{plot_name}_{date_str}.png', dpi=600)

    plt.show()

# Example usage
base_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets'
folder_labels = {
    'Ralph_1': 'Ralph',
}
hall_sensor_col = 'CH13(Hall)'
current_col = 'Magna_1_current'
voltage_col_1 = 'CH6(V1-V2 (Amp x1000))'
voltage_col_2 = 'CH12(OutAmp3)'
voltage_divide_1 = 1000
voltage_divide_2 = 1
plot_title = ''
plot_name = 'Ralph_1'

colors = {
    'set1': {'field': 'tab:blue', 'voltage': 'tab:red'},
    'set2': {'field': 'tab:orange', 'voltage': 'tab:pink'},
    'set3': {'field': 'tab:green', 'voltage': 'tab:olive'},
    'set4': {'field': 'tab:purple', 'voltage': 'tab:brown'},
    'set5': {'field': 'tab:cyan', 'voltage': 'tab:gray'}
}

overlay_plots(base_path, folder_labels, hall_sensor_col, current_col, voltage_col_1, voltage_col_2, voltage_divide_1, voltage_divide_2, plot_title)