import pandas as pd

# ================================
#  CONFIGURATION
# ================================

FILE_PATH = '/Users/fionnferreira/polybox/Shared/BarnesGroup/Projects/Magnet_Fabrication/Nitrogen Magnets/Fionn/Mgn_001_Niamh_1x10m_Theva_FF_040225_processed'

# ================================

def load_data(file_path):
    """
    Loads the LabVIEW raw data file and returns a pandas DataFrame.
    """
    with open(file_path, 'r') as f:
        first_line = f.readline()
    skip_rows = 1 if first_line.startswith("Title") else 0

    df = pd.read_csv(file_path, delimiter=';', skiprows=skip_rows, header=0)

    # Remove columns that contain only NaN values
    df = df.loc[:, (df != 0.0).any(axis=0)]
    df = df.dropna(axis=1, how='all')

    # Remove the first row (row 0)
    df = df.drop(index=0)
    df = df.drop(index=1)

    # Update column names.
    def flatten_col(col):
        if isinstance(col, tuple):
            # If it's a tuple, join the parts.
            return ' '.join([str(item).strip() for item in col if pd.notna(item) and str(item).strip() != ""])
        elif isinstance(col, str):
            # If it's already a string, just strip any extra whitespace.
            return col.strip()
        else:
            return str(col)

    df.columns = [flatten_col(col) for col in df.columns]
    return df

def main():
    # Load the data from file.
    df = load_data(FILE_PATH)

    # Print available columns for reference.
    print("Available columns:")
    for col in df.columns:
        print(col)

    print("\nDataFrame head:")
    print(df.head())

if __name__ == '__main__':
    main()