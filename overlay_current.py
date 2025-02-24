import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

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

# Define the function to overlay plots from multiple folders with custom labels
def overlay_plots(base_path, folder_labels, hall_sensor_col, current_col, plot_title):
    plt.figure(figsize=(10, 7))

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
        'grid.linestyle': '--',
        'font.family': 'serif',
        'font.serif': 'Times New Roman',
        'font.size': 16,
        'axes.titlesize': 16,
        'axes.labelsize': 16,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 14,
    })

    for folder, label in folder_labels.items():
        folder_path = os.path.join(base_path, folder)
        cleaned_csv_path = find_cleaned_csv(folder_path)

        if cleaned_csv_path:
            df = load_and_process_file(cleaned_csv_path)
            plt.plot(df[current_col], abs(df[hall_sensor_col]), label=label)
        else:
            print(f"No cleaned CSV file found in folder: {folder}")

    plt.xlabel('I (A)')
    plt.ylabel('B (T)')
    plt.title(plot_title)
    plt.legend()
    date_str = datetime.now().strftime('%d%m%Y')
    plt.savefig(f'Plots/{plot_name}_{date_str}.png', dpi=600)
    plt.show()


# Example usage
base_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets'
folder_labels = {
    'Mgn_JSFF_b': 'Shanghai Leonardo',
}
hall_sensor_col = 'CH9(Hall sensor 1)'
current_col = 'Magna_1_current'
plot_title = ''
plot_name = 'Mgn_JSFF_b'

overlay_plots(base_path, folder_labels, hall_sensor_col, current_col, plot_title)