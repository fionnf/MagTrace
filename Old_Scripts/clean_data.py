import pandas as pd
import matplotlib.pyplot as plt
import os
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
    skip_rows = 1
    df = pd.read_csv(file_path, delimiter=';', skiprows=skip_rows, header=[0, 1])
    df = df.dropna(axis=1, how='all')
    df.columns = [flatten_col(col) for col in df.columns]
    df = df.apply(pd.to_numeric, errors='coerce')
    df['Timestamp'] = df['Timestamp'] / 1000  # Convert to seconds
    df['Timestamp'] = df['Timestamp'] / 60    # Convert to minutes
    print("Column Headers:", df.columns)
    return df

# Define the function to apply a Savitzky-Golay filter to remove spikes
def remove_spikes(df, column, window_size=51, polyorder=3):
    df[column] = savgol_filter(df[column], window_size, polyorder)
    return df

# Define the function to filter the DataFrame, plot, and save to CSV
def filter_and_plot(file_path, column, min_time, max_time, window_size=51, polyorder=3, remove_windows=None, divide_voltages=None, plot_voltages=False):
    df = load_and_process_file(file_path)

    df_filtered = df[(df['Timestamp'] >= min_time) & (df['Timestamp'] <= max_time)].copy()
    df_filtered['Timestamp'] -= df_filtered['Timestamp'].min()  # Normalize time

    # Remove specified time windows
    if remove_windows:
        for start, end in remove_windows:
            df_filtered = df_filtered[~((df_filtered['Timestamp'] >= start) & (df_filtered['Timestamp'] <= end))]

    # Apply division for specified voltage channels in given time windows
    if divide_voltages:
        for voltage_col, time_windows in divide_voltages.items():
            if voltage_col in df_filtered.columns:
                for start, end in time_windows:
                    mask = (df_filtered['Timestamp'] >= start) & (df_filtered['Timestamp'] <= end)
                    df_filtered.loc[mask, voltage_col] /= 100

    # Remove spikes from the filtered DataFrame
    df_filtered = remove_spikes(df_filtered, column, window_size, polyorder)

    # Save the filtered DataFrame to a new CSV file
    base, ext = os.path.splitext(file_path)
    new_file_path = f"{base}_clean{ext}"
    df_filtered.to_csv(new_file_path, index=False)
    print(f"Filtered data saved to: {new_file_path}")

    # Plot the filtered data
    plt.figure(figsize=(10, 6))
    plt.plot(df_filtered['Timestamp'], abs(df_filtered[column]), label=column)

    # Plot voltage channels only if plot_voltages is True
    if plot_voltages and divide_voltages:
        for voltage_col in divide_voltages.keys():
            if voltage_col in df_filtered.columns:
                plt.plot(df_filtered['Timestamp'], abs(df_filtered[voltage_col]), label=voltage_col)

    plt.xlabel('Time (min)')
    plt.ylabel('Value')
    plt.title('Filtered Data Plot')
    plt.legend()
    plt.show()

# Example usage
file_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets/Ralph_1/Ralph 2x10m Shanghai He 052225 processed (2)'
column = 'CH13(Hall)'
min_time = 0
max_time = 600
remove_windows = []  # Example time windows to remove [(x, y), (z, w)]
divide_voltages = { #include voltage channels and time windows to divide by 100
    'CH6(V1-V2 (Amp x1000))': [],
}
plot_voltages = False
filter_and_plot(file_path, column, min_time, max_time, remove_windows=remove_windows, divide_voltages=divide_voltages, plot_voltages=plot_voltages)
