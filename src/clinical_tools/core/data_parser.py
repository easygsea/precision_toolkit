import json
import pandas as pd
from clinical_tools.core.variant_metrics import VariantCallMetrics


class HappyDataParser:
    @staticmethod
    def process_hap_py_output(file_path):
        """Process the hap.py output file to extract relevant information for each sample.

        Args:
            file_path (str): Path to the hap.py .summary.csv output file.

        Returns:
            list[VariantCallMetrics]: List of VariantCallMetrics objects containing processed data for each row.
        """

        df = pd.read_csv(file_path)

        results = []
        for _, row in df.iterrows():
            metrics = VariantCallMetrics(
                VariantType=row["Type"],
                VariantCallFilter=row["Filter"],
                TruthTotal=row["TRUTH.TOTAL"],
                TruthTP=int(row["TRUTH.TP"]),
                TruthFN=int(row["TRUTH.FN"]),
                QueryTotal=int(row["QUERY.TOTAL"]),
                QueryTP=int(
                    row["TRUTH.TP"]
                ),  # hap.py TRUTH.TP is used for both TruthTP and QueryTP
                QueryFP=int(row["QUERY.FP"]),
            )
            results.append(metrics)
        return results


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
