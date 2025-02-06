import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# ================================
#  CONFIGURATION
# ================================

FILE_PATH = '/Users/fionnferreira/polybox/Shared/BarnesGroup/Projects/Magnet_Fabrication/Nitrogen Magnets/Fionn/Mgn_001_Niamh_1x10m_Theva_FF_040225_processed'

# ================================

def load_data(file_path):
    """
    Loads a LabVIEW raw data file with two header rows and returns a pandas DataFrame.

    The two header rows are combined into a single header in the format:
        Name(Unit)
    For example, if the first header row is "Time" and the second is "s", the combined header becomes "Time(s)".
    """
    # Check if the first line is a title
    with open(file_path, 'r') as f:
        first_line = f.readline()
    skip_rows = 1 if first_line.startswith("Title") else 0

    # Read the CSV file using two header rows.
    df = pd.read_csv(file_path, delimiter=';', skiprows=skip_rows, header=[0, 1])

    # Drop columns that are entirely empty.
    df = df.dropna(axis=1, how='all')

    # Define a function to combine header tuples.
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

    # Apply the flattening to all columns.
    df.columns = [flatten_col(col) for col in df.columns]

    return df


def plot_columns(df, x_column, y_columns, x_label=None, y_label="Value", title=None):
    plt.figure(figsize=(10, 6))

    # Plot each y-axis column
    for y_col in y_columns:
        try:
            # Convert the y-axis data to numeric (non-numeric values become NaN)
            y_data = pd.to_numeric(df[y_col], errors="coerce")
        except Exception as e:
            print(f"Error converting column '{y_col}' to numeric: {e}")
            y_data = df[y_col]
        plt.plot(df[x_column], y_data, label=y_col)

    # Set axis labels and title
    if x_label is None:
        x_label = x_column
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if title is None:
        title = f"Plot of {', '.join(y_columns)} vs {x_column}"
    plt.title(title)

    ax = plt.gca()  # Get the current axis
    ax.xaxis.set_major_locator(MaxNLocator(integer=False, nbins=10))

    plt.legend()
    plt.grid(True)
    plt.show()


def main():
    # Load the data
    df = load_data(FILE_PATH)

    # Print available columns for reference.
    print("Available columns:")
    for col in df.columns:
        print(" -", col)

    # ===== Option 1: Hard-code column names =====
    # Uncomment and update these lines if you prefer hard-coded values.
    # x_column = "Time"
    # y_columns = ["Bx_MV2", "By_MV2"]

    # ===== Option 2: Interactive Input =====
    x_column = input("\nEnter the column name for the x-axis: ").strip()
    y_columns_input = input("Enter the column name(s) for the y-axis (comma separated): ")
    y_columns = [col.strip() for col in y_columns_input.split(",")]



    # Call the separate plotting function
    plot_columns(df, x_column, y_columns)


if __name__ == '__main__':
    main()