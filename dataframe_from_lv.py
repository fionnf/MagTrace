import pandas as pd
import matplotlib.pyplot as plt

plot_title = 'Mgn_002'

# Define the window for the x-axis (time in minutes)
min_time = 0  # Set your desired minimum time in minutes
max_time = 31  # Set your desired maximum time in minutes

# Specify the file path
file_path = '/Users/fionnferreira/Library/CloudStorage/GoogleDrive-fionnferreira@gmail.com/My Drive/Barnes Group/Magnets/Mgn_002/Mgn_002_Anna_1x10m_Theva_FF_050225_processed'



# Define the function to flatten header columns
def flatten_col(col):
    """
    If the header column is a tuple (from two header rows), combine it as:
        Name(Unit)
    If the second part is missing or empty, only the first part is used.
    If the header is already a string, just return it stripped.
    """
    if isinstance(col, tuple):
        # Extract the two parts (assume first is the variable name and second is the unit)
        first = str(col[0]).strip() if pd.notna(col[0]) else ""
        second = str(col[1]).strip() if pd.notna(col[1]) else ""
        # If there is a nonempty unit and it differs from the name, combine them.
        if second and second != first:
            return f"{first}({second})"
        else:
            return first
    else:
        return str(col).strip()

# Define the function to load and process the file
def load_and_process_file(file_path):
    # Skip the header rows and combine them into one
    skip_rows = 1
    df = pd.read_csv(file_path, delimiter=';', skiprows=skip_rows, header=[0, 1])

    # Drop columns that are entirely empty
    df = df.dropna(axis=1, how='all')

    # Apply the flatten_col function to the columns
    df.columns = [flatten_col(col) for col in df.columns]

    # Convert everything to ordinary numbers, coercing non-numeric values into NaN
    df = df.apply(pd.to_numeric, errors='coerce')

    return df

# Load and process the file
df = load_and_process_file(file_path)

# Display the first few rows of the DataFrame
print(df.head())
print(df.columns)

# Convert 'Timestamp' from milliseconds to minutes
df['Timestamp'] = df['Timestamp'] / 1000  # Convert to seconds
df['Timestamp'] = df['Timestamp'] / 60    # Convert to minutes

# Create the plot with the first y-axis (ax1)
fig, ax1 = plt.subplots()

# Plot 'Timestamp' vs 'CH9 (Hall sensor 1)' on the first y-axis
ax1.plot(df['Timestamp'], df['CH9(Hall sensor 1)'], label='B (T)', color='b')
ax1.set_xlabel('Time (min)')
ax1.set_ylabel('B (T)', color='b')
ax1.tick_params(axis='y', labelcolor='b')

# Create the second y-axis (ax2)
ax2 = ax1.twinx()
ax2.plot(df['Timestamp'], abs(df['CH10(OutAmp1)']/100), label='Voltage (mV)', color='r')
ax2.set_ylabel('Voltage (mV)', color='r', labelpad=0)
ax2.set_ylim(0, 5)
ax2.tick_params(axis='y', labelcolor='r')

# Create the third y-axis (ax3)
ax3 = ax1.twinx()
# Offset the third y-axis slightly to avoid overlap with ax2
#ax3.spines['right'].set_position(('outward', 60))
ax3.set_ylabel('CH11', color='g', labelpad=20)
# Plot 'Timestamp' vs another column (e.g., CH11) on the third y-axis
ax3.plot(df['Timestamp'], df['Magna_1_current'], label='I (A)', color='g')
ax3.set_ylabel('I (A)', color='g')
ax3.tick_params(axis='y', labelcolor='g')

# Set the window for x-axis limits
ax1.set_xlim(min_time, max_time)

# Add title and legend
plt.title(plot_title)

# Display the plot
fig.tight_layout()  # To ensure everything fits without overlap
# Save the plot to a file (e.g., PNG, PDF, SVG)
plt.savefig(f'Plots/{plot_title}.png', dpi=300)
plt.show()

