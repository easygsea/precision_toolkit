import pandas as pd
from clinical_tools.core.metrics.variant import VariantCallMetrics


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