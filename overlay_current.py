import pandas as pd
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
    return df

# Define the function to find the cleaned CSV file in a folder
def find_cleaned_csv(folder_path):
    for file_name in os.listdir(folder_path):
        if 'clean' in file_name:
            return os.path.join(folder_path, file_name)
    return None

# Define the function to overlay plots from multiple folders
def overlay_plots(base_path, folders, hall_sensor_col, current_col):
    plt.figure(figsize=(10, 6))

    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        cleaned_csv_path = find_cleaned_csv(folder_path)

        if cleaned_csv_path:
            df = load_and_process_file(cleaned_csv_path)
            plt.plot(df[current_col], abs(df[hall_sensor_col]), label=folder)
        else:
            print(f"No cleaned CSV file found in folder: {folder}")

    plt.xlabel('I (A)')
    plt.ylabel('B (T)')
    plt.title('1 M THEVA Coils')
    plt.legend()
    plt.show()

# Example usage
base_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets'
folders = ['Mgn_006', 'Mgn_007', 'Mgn_008']
hall_sensor_col = 'CH9(Hall sensor 1)'
current_col = 'Magna_1_current'

overlay_plots(base_path, folders, hall_sensor_col, current_col)