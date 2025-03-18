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
def overlay_plots(base_path, folder_labels, folder_colors, hall_sensor_col, current_col, plot_title):
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
        'grid.linestyle': '',
        'font.serif': 'Arial',
        'font.size': 18,
        'axes.titlesize': 18,
        'axes.labelsize': 18,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'legend.fontsize': 18,
    })

    for folder, label in folder_labels.items():
        folder_path = os.path.join(base_path, folder)
        cleaned_csv_path = find_cleaned_csv(folder_path)

        if cleaned_csv_path:
            df = load_and_process_file(cleaned_csv_path)
            plt.scatter(df[current_col], abs(df[hall_sensor_col]), label=label, s=15, color=folder_colors[folder])
        else:
            print(f"No cleaned CSV file found in folder: {folder}")

    plt.xlabel('I (A)')
    plt.ylabel('B (T)')
    plt.title(plot_title)
    plt.legend()
    plt.minorticks_on()
    plt.tick_params(top=True, labeltop=False, right=True, labelright=False)
    plt.tick_params(which='minor', top=True, right=True)
    date_str = datetime.now().strftime('%d%m%Y')
    plt.savefig(f'Plots/{plot_name}_{date_str}.png', dpi=600)
    plt.show()


# Example usage
base_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets'
folder_labels = {
    #'Mgn_013': '1 x 5m (iii)',
    'Mgn_JSFF_b': '2 x 200m (i+ii)',
    'Mgn_014a': '1 x 200m (i)',
    'Mgn_014b': '1 x 200m (ii)',
    #'Mgn_015d': '2 x 45m (piggy 3 r)',
    #'Piggy_3': '2 x 45m (piggy 3 u)',
    #'Mgn_015c': '2 x 45m (piggy 3)',
    #'Piggy_2': '1 x 45m (piggy 2)',
    #'Piggy_1': '1 x 45m (piggy 1)',
}

folder_colors = {
    #'Mgn_013': 'tab:green',
    'Mgn_JSFF_b': 'tab:purple',
    'Mgn_014a': 'tab:red',
    'Mgn_014b': 'tab:blue',
    #'Mgn_015d': 'tab:brown',
    #'Piggy_3': 'tab:blue',
    #'Mgn_015c': 'tab:pink',
    #'Piggy_2': 'tab:cyan',
    #'Piggy_1': 'tab:olive',
}

hall_sensor_col = 'CH9(Hall sensor 1)'
current_col = 'Magna_1_current'
plot_title = ''
plot_name = 'Leonardo'

overlay_plots(base_path, folder_labels, folder_colors, hall_sensor_col, current_col, plot_title)