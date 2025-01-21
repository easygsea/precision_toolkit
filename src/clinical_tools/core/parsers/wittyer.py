import json
import pandas as pd
from clinical_tools.core.metrics.variant import VariantCallMetrics


class WittyerDataParser:
    @staticmethod
    def process_witty_er_output(file_path):
        """Process the Wittyer output JSON file to extract relevant information for each sample.

        Args:
            file_path (str): Path to the Wittyer.Stats.json output file.

        Returns:
            List[VariantCallMetrics]: List of VariantCallMetrics objects for each type of stats found.
        """
        with open(file_path, "r") as file:
            data = json.load(file)

        results = []
        if "PerSampleStats" in data:
            for sample in data["PerSampleStats"]:
                for stats in sample["OverallStats"]:
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
        return results