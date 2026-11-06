"""Parser for Witty.er output."""

import json
import logging
from collections.abc import Sequence
from pathlib import Path

from precision_toolkit.core.metrics.variant import VariantCallMetrics

logger = logging.getLogger(__name__)


class WittyerDataParser:
    """Parser for Wittyer output."""

    @staticmethod
    def process_witty_er_output(file_path: Path | str) -> Sequence[VariantCallMetrics]:
        """Process the Wittyer output JSON file to extract metrics information.

        Args:
            file_path: Path to the Wittyer.Stats.json output file

        Returns:
            Sequence of VariantCallMetrics objects containing processed data
        """
        logger.info(f"Processing Wittyer output file: {file_path}")

        try:
            with open(file_path) as file:
                data = json.load(file)

            results = []
            if "PerSampleStats" in data:
                for sample in data["PerSampleStats"]:
                    for stats in sample["OverallStats"]:
                        try:
                            metrics = VariantCallMetrics(
                                VariantType=stats["StatsType"],
                                VariantCallFilter="All",
                                TruthTotal=stats["TruthTotalCount"],
                                TruthTP=stats["TruthTpCount"],
                                TruthFN=stats["TruthFnCount"],
                                QueryTotal=stats["QueryTotalCount"],
                                QueryTP=stats["QueryTpCount"],
                                QueryFP=stats["QueryFpCount"],
                            )
                            results.append(metrics)
                        except (KeyError, TypeError) as e:
                            logger.warning(f"Error processing stats: {e!s}")

            logger.info(f"Successfully processed {len(results)} metrics")
            return results

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e!s}")
            raise
