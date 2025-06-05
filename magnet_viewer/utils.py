# utils.py

def flatten_col(col):
    """
    Flatten multi-level column headers from pandas read_csv into a readable string.
    If col is a tuple like ('Current', 'A'), returns 'Current(A)'.
    """
    if isinstance(col, tuple):
        first = str(col[0]).strip() if col[0] else ""
        second = str(col[1]).strip() if col[1] else ""
        return f"{first}({second})" if second and second != first else first
    return str(col).strip()


def get_scale_factor(scale_text):
    """
    Convert scale label (used in dropdowns) into a numeric factor.
    E.g. '÷1000' -> 0.001
    """
    return {
        '÷10': 0.1,
        '÷100': 0.01,
        '÷1000': 0.001,
        'mV': 1e-3,
        'mV×100': 1e-3 / 100,
        'mV×1000': 1e-3 / 1000
    }.get(scale_text, 1.0)