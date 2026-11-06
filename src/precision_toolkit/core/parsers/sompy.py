"""Parser for som.py output."""

import logging
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from precision_toolkit.core.metrics.variant import VariantCallMetrics

logger = logging.getLogger(__name__)


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
        logger.info(f"Processing som.py output file: {file_path}")

        df = pd.read_csv(file_path)
        logger.debug(f"Successfully loaded CSV with {len(df)} rows")

        results = []
        for idx, row in df.iterrows():
            try:
                metrics = VariantCallMetrics(
                    VariantType=row["type"],
                    VariantCallFilter="NA",
                    TruthTotal=int(row["total.truth"]),
                    TruthTP=int(row["tp"]),
                    TruthFN=int(row["fn"]),
                    QueryTotal=int(row["total.query"]),
                    QueryTP=int(row["tp"]),
                    QueryFP=int(row["fp"]),
                )
                results.append(metrics)
            except (KeyError, TypeError, ValueError, OverflowError) as e:
                logger.warning(f"Error processing row {idx}: {e!s}")

        logger.info(f"Successfully processed {len(results)} metrics")
        return results
