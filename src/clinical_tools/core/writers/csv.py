import logging
from pathlib import Path

import pandas as pd


def pandas_to_csv(df: pd.DataFrame, output_file: str | Path) -> None:
    """Save DataFrame to CSV file.

    Args:
        df: DataFrame to save
        output_file: Path to output file
    """
    df.to_csv(output_file, index=False)
    logging.info(f"Table saved to {output_file}")
