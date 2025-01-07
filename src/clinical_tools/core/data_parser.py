import json
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
    results = []
    with open(file_path, 'r') as file:
      for line in file:
        if line.strip():
          parts = line.strip().split(',')
          metrics = VariantCallMetrics(
            VariantType=parts[0],
            VariantCallFilter=parts[1],
            TruthTotal=int(parts[2]),
            TruthTP=int(parts[3]),
            TruthFN=int(parts[4]),
            QueryTotal=int(parts[5]),
            QueryTP=int(parts[3]),  # This seems to be reused; confirm logic
            QueryFP=int(parts[6]),
            Recall=float(parts[10]),
            Precision=float(parts[11]),
            F1Score=float(parts[13]),
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
    with open(file_path, 'r') as file:
      data = json.load(file)

    results = []
    if 'PerSampleStats' in data:
      for sample in data['PerSampleStats']:
        for stats in sample['OverallStats']:
          metrics = VariantCallMetrics(
            VariantType=stats['StatsType'],
            VariantCallFilter="All",
            TruthTotal=stats['TruthTotalCount'],
            TruthTP=stats['TruthTpCount'],
            TruthFN=stats['TruthFnCount'],
            QueryTotal=stats['QueryTotalCount'],
            QueryTP=stats['QueryTpCount'],
            QueryFP=stats['QueryFpCount'],
            Sensitivity=stats['Recall'],
            Precision=stats['Precision'],
            F1Score=stats['Fscore']
          )
          results.append(metrics)
    return results
