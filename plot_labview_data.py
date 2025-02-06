import pandas as pd
import matplotlib.pyplot as plt
import argparse


def load_data(file_path):
    """
    Loads the LabVIEW raw data file.
    Assumes the first line is a title if it starts with "Title",
    and that the next two lines are header rows with semicolon-delimited fields.
    The headers are flattened into one level.
    """
    # Check if the first line is a title line
    with open(file_path, 'r') as f:
        first_line = f.readline()
    if first_line.startswith("Title"):
        skip_rows = 1
    else:
        skip_rows = 0

    # Read the CSV file:
    # - delimiter is ";"
    # - skip the title line (if present)
    # - use the next two rows as headers (index 0 and 1)
    df = pd.read_csv(file_path, delimiter=';', skiprows=skip_rows, header=[0, 1])

    # Flatten the MultiIndex columns by joining the two header rows.
    # This produces column names like "Timestamp", "Time", "Magna_1_current", etc.
    df.columns = [
        ' '.join([str(item).strip() for item in tup if pd.notna(item) and item != ""])
        for tup in df.columns.values
    ]

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Plot data from a LabVIEW raw data file with semicolon-separated values."
    )
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help="Path to the raw data file."
    )
    parser.add_argument(
        '--x',
        type=str,
        default="Time",
        help="Column name to use for the x-axis (default: 'Time')."
    )
    parser.add_argument(
        '--y',
        type=str,
        nargs='+',
        required=True,
        help="One or more column names to plot on the y-axis."
    )
    args = parser.parse_args()

    # Load the data from file
    df = load_data(args.file)

    # Print available columns to help you decide which to plot
    print("Available columns:")
    for col in df.columns:
        print(" -", col)

    # Try to convert the x-axis column to datetime first.
    # If that fails, try converting it to a numeric type.
    try:
        df[args.x] = pd.to_datetime(df[args.x])
    except Exception as e:
        print(f"Could not convert column '{args.x}' to datetime: {e}")
        try:
            df[args.x] = pd.to_numeric(df[args.x], errors='coerce')
        except Exception as e2:
            print(f"Could not convert column '{args.x}' to numeric: {e2}")

    plt.figure(figsize=(10, 6))

    # Plot each specified y-axis column.
    for y_col in args.y:
        try:
            # Convert y-axis data to numeric (coercing errors to NaN)
            y_data = pd.to_numeric(df[y_col], errors='coerce')
        except Exception as e:
            print(f"Error converting column '{y_col}' to numeric: {e}")
            y_data = df[y_col]
        plt.plot(df[args.x], y_data, label=y_col)

    plt.xlabel(args.x)
    plt.ylabel("Value")
    plt.title("Plot of " + ", ".join(args.y) + " vs " + args.x)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()