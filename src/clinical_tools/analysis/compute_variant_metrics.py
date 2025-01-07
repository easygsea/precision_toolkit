from collections import defaultdict
from clinical_tools.core.data_parser import (
    HappyDataParser,
    WittyerDataParser,
    VariantCallMetrics,
)
from clinical_tools.core.variant_metrics import ConcordanceMetrics, VariantCallMetrics


def load_data_from_files(files, data_type="happy"):
    """Load data from files based on the specified data type.

    Args:
      files (list): List of paths to the files to be loaded.
      data_type (str): Specifies whether to load 'happy' or 'wittyer' data.
                       Default is 'happy'.

    Returns:
      list[VariantCallMetrics]: List of parsed metrics.

    Raises:
      ValueError: If an invalid data_type is provided.
    """
    if data_type == "happy":
        parser = HappyDataParser.process_hap_py_output
    elif data_type == "wittyer":
        parser = WittyerDataParser.process_wittyer_output
    else:
        raise ValueError("data_type must be either 'happy' or 'wittyer'")

    all_metrics = []
    for file_path in files:
        all_metrics.extend(parser(file_path))

    return all_metrics


def compute_concordance_and_ci(metrics):
    """Compute concordance and confidence intervals grouped by VariantType and VariantCallFilter.

    Args:
      metrics (list[VariantCallMetrics]): Parsed metrics across samples.

    Returns:
      dict: A dictionary where keys are (VariantType, VariantCallFilter), and values are tuples:
            (concordance, lower_ci, upper_ci)
    """
    grouped_metrics = defaultdict(list)
    for metric in metrics:
        grouped_metrics[(metric.VariantType, metric.VariantCallFilter)].append(metric)

    results = {}
    for (variant_type, variant_filter), group in grouped_metrics.items():
        total_truth_tp = sum(metric.TruthTP for metric in group)
        total_truth_fn = sum(metric.TruthFN for metric in group)
        total_query_tp = sum(metric.QueryTP for metric in group)
        total_query_fp = sum(metric.QueryFP for metric in group)

        aggregated_metrics = VariantCallMetrics(
            VariantType=variant_type,
            VariantCallFilter=variant_filter,
            TruthTotal=total_truth_tp + total_truth_fn,
            TruthTP=total_truth_tp,
            TruthFN=total_truth_fn,
            QueryTotal=total_query_tp + total_query_fp,
            QueryTP=total_query_tp,
            QueryFP=total_query_fp,
        )

        analysis = ConcordanceMetrics(aggregated_metrics)
        concordance = analysis.concordance
        ci_lower, ci_upper = analysis.confidence_interval()

        results[(variant_type, variant_filter)] = (
            aggregated_metrics.TruthTP,
            aggregated_metrics.TruthFN,
            aggregated_metrics.QueryFP,
            concordance,
            ci_lower,
            ci_upper,
        )

    return results


def process_variant_metrics(file_paths, data_type):
    """Process variant metrics and compute confidence intervals.

    Args:
        file_paths (list): List of file paths to process.
        data_type (str): Specifies whether the files are 'happy' or 'wittyer' data.

    Returns:
        dict: Variant metrics grouped by VariantType and VariantCallFilter.
    """
    metrics = load_data_from_files(file_paths, data_type=data_type)

    concordance_results = compute_concordance_and_ci(metrics)

    return concordance_results
