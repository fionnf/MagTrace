import pandas as pd
import matplotlib.pyplot as plt


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

# Specify the file path
file_path = '/Users/fionnferreira/polybox/Shared/BarnesGroup/Projects/Magnet_Fabrication/Nitrogen Magnets/Fionn/Mgn_001_Niamh_1x10m_Theva_FF_040225'

# Load and process the file
df = load_and_process_file(file_path)

# Display the first few rows of the DataFrame
print(df.head())

# Plotting 'Timestamp' vs 'CH9 (Hall sensor 1)'

min_time = 15
max_time = 40

df['Timestamp'] = df['Timestamp']/1000
df['Timestamp'] = df['Timestamp']/60

# Plotting 'Timestamp' vs 'CH9 (Hall sensor 1)'
plt.plot(df['Timestamp'], df['CH9(Hall sensor 1)'], label='B (T)')

# Adding labels and title
plt.xlabel('Time (min)')
plt.ylabel('CH9 (Hall sensor 1)')
plt.title('Timestamp vs CH9 (Hall sensor 1)')

plt.xlim(min_time, max_time)

# Display the plot
plt.tight_layout()  # To ensure everything fits without overlap
plt.legend()
plt.show()

