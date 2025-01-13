import logging
import pandas as pd


def pandas_to_csv(df: pd.DataFrame, output_file: str) -> None:
    """
    Save pandas DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The pandas DataFrame.
        output_file (str): The path to the output CSV file.

    Returns:
        None
    """
    df.to_csv(output_file, index=False)
    logging.info(f"Table saved to {output_file}")
