import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.colors import Normalize

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
    if 'Magna_2_current' not in df.columns:
        df['Magna_2_current'] = 0
    return df

# Define the function to find the cleaned CSV file in a folder
def find_cleaned_csv(folder_path):
    for file_name in os.listdir(folder_path):
        if 'clean' in file_name:
            return os.path.join(folder_path, file_name)
    return None

# Define the function to create a scatter plot
def create_scatter_plot(all_data, plot_title):
    current_1 = all_data['current_1']
    current_2 = all_data['current_2']
    field_strength = all_data['field_strength']

    plt.figure(figsize=(10, 8))
    cmap = plt.get_cmap('viridis')
    scatter = plt.scatter(current_1, current_2, c=field_strength, cmap=cmap, s=300, edgecolor='none', linewidth=1)
    plt.colorbar(scatter, label='Field Strength (T)')
    plt.xlabel('Outer Coil Current (A)')
    plt.ylabel('Inner Coil Current (A)')
    plt.title(plot_title)
    plt.show()

# Define the function to process multiple subfolders
def process_subfolders(base_path, subfolders, current_col_1, current_col_2, field_col, plot_title, swap_datasets=None):
    if swap_datasets is None:
        swap_datasets = []

    all_data = {'current_1': [], 'current_2': [], 'field_strength': []}
    seen_coordinates = set()  # Track seen coordinate pairs

    for subfolder in subfolders:
        folder_path = os.path.join(base_path, subfolder)
        cleaned_csv_path = find_cleaned_csv(folder_path)

        if cleaned_csv_path:
            df = load_and_process_file(cleaned_csv_path)
            for _, row in df.iterrows():
                # Determine the coordinates based on whether the dataset is swapped
                if subfolder in swap_datasets:
                    coord = (row[current_col_2], row[current_col_1])
                else:
                    coord = (row[current_col_1], row[current_col_2])

                # Skip if the coordinate pair has already been seen
                if coord in seen_coordinates:
                    continue

                # Add the coordinate pair to the seen set
                seen_coordinates.add(coord)

                # Append the data
                all_data['current_1'].append(coord[0])
                all_data['current_2'].append(coord[1])
                all_data['field_strength'].append(abs(row[field_col]))  # Ensure field values are positive
        else:
            print(f"No cleaned CSV file found in folder: {subfolder}")

    create_scatter_plot(all_data, plot_title)

# Example usage
base_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets'
subfolders = ['Mgn013_020_rerun']
current_col_1 = 'Magna_1_current'
current_col_2 = 'Magna_2_current'
field_col = 'CH9(Hall sensor 1)'
plot_title = 'Field Scatter Plot'
swap_datasets = ['Mgn_012']  # List of subfolders where Magna_1 and Magna_2 are swapped

process_subfolders(base_path, subfolders, current_col_1, current_col_2, field_col, plot_title, swap_datasets)