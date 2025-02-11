import json
import logging
from collections.abc import Sequence
from pathlib import Path

from clinical_tools.core.metrics.variant import VariantCallMetrics


class WittyerDataParser:
    @staticmethod
    def process_witty_er_output(file_path: Path | str) -> Sequence[VariantCallMetrics]:
        """Process the Wittyer output JSON file to extract metrics information.

        Args:
            file_path: Path to the Wittyer.Stats.json output file

        Returns:
            Sequence of VariantCallMetrics objects containing processed data
        """
        logging.info(f"Processing Wittyer output file: {file_path}")

        try:
            with open(file_path, "r") as file:
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
                        except Exception as e:
                            logging.warning(f"Error processing stats: {str(e)}")

            logging.info(f"Successfully processed {len(results)} metrics")
            return results

        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {str(e)}")
            raise
