"""Parser for hap.py output."""

import logging
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from clinical_tools.core.metrics.variant import VariantCallMetrics


class HappyDataParser:
    @staticmethod
    def process_hap_py_output(file_path: Path | str) -> Sequence[VariantCallMetrics]:
        """Process the hap.py output file to extract relevant information.

        Args:
            file_path: Path to the hap.py .summary.csv output file.

        Returns:
            Sequence of VariantCallMetrics objects containing processed data.
        """
        logging.info(f"Processing hap.py output file: {file_path}")

        try:
            df = pd.read_csv(file_path)
            logging.debug(f"Successfully loaded CSV with {len(df)} rows")

            results = []
            for idx, row in df.iterrows():
                try:
                    metrics = VariantCallMetrics(
                        VariantType=row["Type"],
                        VariantCallFilter=row["Filter"],
                        TruthTotal=row["TRUTH.TOTAL"],
                        TruthTP=int(row["TRUTH.TP"]),
                        TruthFN=int(row["TRUTH.FN"]),
                        QueryTotal=int(row["QUERY.TOTAL"]),
                        QueryTP=int(row["TRUTH.TP"]),
                        QueryFP=int(row["QUERY.FP"]),
                    )
                    results.append(metrics)
                except Exception as e:
                    logging.warning(f"Error processing row {idx}: {str(e)}")

            logging.info(f"Successfully processed {len(results)} metrics")
            return results

        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {str(e)}")
            raise
