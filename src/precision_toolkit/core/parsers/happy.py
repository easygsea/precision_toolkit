"""Parser for hap.py output."""

import logging
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from precision_toolkit.core.metrics.variant import VariantCallMetrics

logger = logging.getLogger(__name__)


class HappyDataParser:
    """Parser for hap.py output."""

    @staticmethod
    def process_hap_py_output(file_path: Path | str) -> Sequence[VariantCallMetrics]:
        """Process the hap.py output file to extract relevant information.

        Args:
            file_path: Path to the hap.py .summary.csv output file.

        Returns:
            Sequence of VariantCallMetrics objects containing processed data.
        """
        logger.info(f"Processing hap.py output file: {file_path}")

        df = pd.read_csv(file_path)
        logger.debug(f"Successfully loaded CSV with {len(df)} rows")

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
            except (KeyError, TypeError, ValueError, OverflowError) as e:
                logger.warning(f"Error processing row {idx}: {e!s}")

        logger.info(f"Successfully processed {len(results)} metrics")
        return results
