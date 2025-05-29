"""Parser for som.py output."""

import logging
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from clinical_tools.core.metrics.variant import VariantCallMetrics


class SompyDataParser:
    """Parser for som.py output."""

    @staticmethod
    def process_sompy_output(file_path: Path | str) -> Sequence[VariantCallMetrics]:
        """Process the som.py output file to extract relevant information.

        Args:
            file_path: Path to the som.py .stats.csv output file.

        Returns:
            Sequence of VariantCallMetrics objects containing processed data.
        """
        logging.info(f"Processing som.py output file: {file_path}")

        try:
            df = pd.read_csv(file_path)
            logging.debug(f"Successfully loaded CSV with {len(df)} rows")

            results = []
            for idx, row in df.iterrows():
                try:
                    metrics = VariantCallMetrics(
                        VariantType=row["type"],
                        VariantCallFilter="PASS",  # som.py doesn't have filter column
                        TruthTotal=int(row["total.truth"]),
                        TruthTP=int(row["tp"]),
                        TruthFN=int(row["fn"]),
                        QueryTotal=int(row["total.query"]),
                        QueryTP=int(row["tp"]),
                        QueryFP=int(row["fp"]),
                    )
                    results.append(metrics)
                except Exception as e:
                    logging.warning(f"Error processing row {idx}: {str(e)}")

            logging.info(f"Successfully processed {len(results)} metrics")
            return results

        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {str(e)}")
            raise
