import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

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
    # Check if Magna_2_current column exists, if not create it with zeros
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
def create_scatter_plot(df, current_col_1, current_col_2, field_col, plot_title):
    # Extract the data
    current_1 = df[current_col_1].values
    current_2 = df[current_col_2].values
    field_strength = np.abs(df[field_col].values)  # Ensure field values are positive

    # Plot the scatter plot
    plt.figure(figsize=(10, 8))
    cmap = plt.get_cmap('viridis')
    scatter = plt.scatter(current_1, current_2, c=field_strength, cmap=cmap, s=100, edgecolor='white', linewidth=1)
    plt.colorbar(scatter, label='Field Strength (T)')
    plt.xlabel('Magna 1 Current (A)')
    plt.ylabel('Magna 2 Current (A)')
    plt.title(plot_title)
    plt.show()

# Define the function to process multiple subfolders
def process_subfolders(base_path, subfolders, current_col_1, current_col_2, field_col, plot_title):
    for subfolder in subfolders:
        folder_path = os.path.join(base_path, subfolder)
        cleaned_csv_path = find_cleaned_csv(folder_path)

        if cleaned_csv_path:
            df = load_and_process_file(cleaned_csv_path)
            create_scatter_plot(df, current_col_1, current_col_2, field_col, f"{plot_title} - {subfolder}")
        else:
            print(f"No cleaned CSV file found in folder: {subfolder}")

# Example usage
base_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets'
subfolders = ['Mgn_017', 'Mgn_018', 'Mgn_011']
current_col_1 = 'Magna_1_current'
current_col_2 = 'Magna_2_current'
field_col = 'CH9(Hall sensor 1)'
plot_title = 'Field Scatter Plot'

process_subfolders(base_path, subfolders, current_col_1, current_col_2, field_col, plot_title)