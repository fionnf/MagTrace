import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.optimize import curve_fit
import numpy as np

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

# Define the function to extract maximum B value and plot against coil length
def plot_max_b_vs_length(base_path, folder_labels, hall_sensor_col):
    lengths = [0.0]
    max_b_values = [0.0]

    for folder, label in folder_labels.items():
        folder_path = os.path.join(base_path, folder)
        cleaned_csv_path = find_cleaned_csv(folder_path)

        if cleaned_csv_path:
            df = load_and_process_file(cleaned_csv_path)
            max_b = abs(df[hall_sensor_col]).max()
            lengths.append(folder_labels[folder])
            max_b_values.append(max_b)
        else:
            print(f"No cleaned CSV file found in folder: {folder}")

    # Convert lengths and max_b_values to numpy arrays
    lengths = np.array(lengths)
    max_b_values = np.array(max_b_values)
    print('lengths:', lengths)
    print('max_b_values:', max_b_values)


    # Plot the data and the fit line
    plt.figure(figsize=(10, 7))
    plt.scatter(lengths, max_b_values, color='tab:blue', s=50, label='Data')
    plt.xlabel('Coil Length (m)')
    plt.ylabel('Maximum B (T)')
    plt.ylim(0, 7)
    plt.title('Maximum B vs Coil Length (double coil)')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'Plots/double_shanghai_trend.png', dpi=600)
    plt.show()

# Example usage
base_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets'
folder_labels = {
    'Mgn_JSFF_b': 200,
    'piggy_3': 45,
}

hall_sensor_col = 'CH9(Hall sensor 1)'

plot_max_b_vs_length(base_path, folder_labels, hall_sensor_col)