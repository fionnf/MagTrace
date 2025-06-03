import pandas as pd
import matplotlib.pyplot as plt

# PLOT PARAMETERS

plot_title = '1m Theva HTS coils'
files_to_plot = [
    {'file_path': '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets/Mgn_006/Mgn_006_Manuel_1x01m_Theva_FF_100225_processed', 'column': 'CH9(Hall sensor 1)', 'min_time': 29, 'max_time': 41, 'color': 'b', 'label': 'Mgn_006'},
    {'file_path': '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets/Mgn_007/Mgn_007_Carolina_1x01m_Theva_FF_110225_processed', 'column': 'CH9(Hall sensor 1)', 'min_time': 44.5, 'max_time': 66, 'color': 'r', 'label': 'Mgn_007'},
    {'file_path': '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets/Mgn_008/Mgn_008_Simone_1x01m_Theva_FF_120225_processed', 'column': 'CH9(Hall sensor 1)', 'min_time': 35, 'max_time': 65, 'color': 'g', 'label': 'Mgn_008'}
]
v_max = 1000  # Set the maximum voltage value for the second y-axis
i_max = 800  # Set the maximum current value for the third y-axis
save = True  # Set to True to save the plot as a file
v_lab_off = 10  # Set the offset for the voltage label on the second y-axis
i_lab_off = 25  # Set the offset for the current label on the third y-axis

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
    return df

# Create the plot
fig, ax1 = plt.subplots()

# Plot each file with its respective time range
for file_info in files_to_plot:
    file_path = file_info['file_path']
    col = file_info['column']
    min_time = file_info['min_time']
    max_time = file_info['max_time']
    color = file_info['color']
    label = file_info['label']
    scale = file_info.get('scale', 1)

    # Load and process the file
    df = load_and_process_file(file_path)

    # Convert 'Timestamp' from milliseconds to minutes
    df['Timestamp'] = df['Timestamp'] / 1000  # Convert to seconds
    df['Timestamp'] = df['Timestamp'] / 60    # Convert to minutes

    # Filter the DataFrame for the specified time range
    df_filtered = df[(df['Timestamp'] >= min_time) & (df['Timestamp'] <= max_time)].copy()
    df_filtered['Timestamp'] -= df_filtered['Timestamp'].min()  # Set start time to zero

    # Plot the column
    ax1.plot(df_filtered['Timestamp'], abs(df_filtered[col]) * scale, label=label, color=color)

# Set labels and title
ax1.set_xlabel('Time (min)')
ax1.set_ylabel('Value')
ax1.set_title(plot_title)
ax1.legend()

# Display the plot
fig.tight_layout()
if save:
    plt.savefig(f'Plots/{plot_title}.png', dpi=600)

plt.show()