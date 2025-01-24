from collections.abc import Sequence

from clinical_tools.core.metrics.variant import (
    ConcordanceMetrics,
    VariantCallMetrics,
)
from clinical_tools.core.parsers.happy import HappyDataParser
from clinical_tools.core.parsers.wittyer import WittyerDataParser


def load_data_from_files(
    files: Sequence[str], 
    data_type: str
) -> Sequence[VariantCallMetrics]:
    """Load data from files based on the specified data type.

    Args:
        files: Sequence of paths to the files to be loaded
        data_type: Type of data to load ('happy' or 'wittyer')

    Returns:
        Sequence of parsed metrics

    Raises:
        ValueError: If no files provided or invalid data_type
    """
    if not files:
        raise ValueError("No files provided")
        
    if data_type == "happy":
        parser = HappyDataParser.process_hap_py_output
    elif data_type == "wittyer":
        parser = WittyerDataParser.process_witty_er_output
    else:
        raise ValueError(f"Unsupported data_type: {data_type}. Must be 'happy' or 'wittyer'")

    all_metrics = []
    for file_path in files:
        try:
            all_metrics.extend(parser(file_path))
        except Exception as e:
            raise RuntimeError(f"Error processing file {file_path}: {str(e)}")

    return all_metrics


def compute_concordance_and_ci(
    metrics: Sequence[VariantCallMetrics]
) -> dict[tuple[str, str], tuple[int, int, int, float, float, float]]:
    """Compute concordance and confidence intervals grouped by variant type and filter.
    
    Args:
        metrics: Sequence of parsed metrics across samples

    Returns:
        Dictionary mapping (variant_type, filter) to metrics tuple:
            truth_tp: Number of true positives in truth set
            truth_fn: Number of false negatives
            query_fp: Number of false positives
            concordance: Concordance rate between 0 and 1
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
    """
    grouped_metrics = {
        (metric.VariantType, metric.VariantCallFilter): []
        for metric in metrics
    }
    
    for metric in metrics:
        key = (metric.VariantType, metric.VariantCallFilter)
        grouped_metrics[key].append(metric)

    return {
        (variant_type, variant_filter): _compute_concordance_and_ci_for_group(group)
        for (variant_type, variant_filter), group in grouped_metrics.items()
    }

def _compute_concordance_and_ci_for_group(
    group: list[VariantCallMetrics]
) -> tuple[int, int, int, float, float, float]:
    """Calculate concordance metrics for a group of variants.
    
    Helper function for compute_concordance_and_ci that processes
    a single group of variants with the same type and filter.

    Args:
        group: List of variant metrics to aggregate, all with same type and filter

    Returns:
        Tuple of metrics:
            truth_tp: Number of true positives in truth set
            truth_fn: Number of false negatives
            query_fp: Number of false positives
            concordance: Concordance rate between 0 and 1
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
    """
    total_truth_tp = sum(metric.TruthTP for metric in group)
    total_truth_fn = sum(metric.TruthFN for metric in group)
    total_query_tp = sum(metric.QueryTP for metric in group)
    total_query_fp = sum(metric.QueryFP for metric in group)

    aggregated_metrics = VariantCallMetrics(
        VariantType=group[0].VariantType,
        VariantCallFilter=group[0].VariantCallFilter,
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

    return (
        aggregated_metrics.TruthTP,
        aggregated_metrics.TruthFN,
        aggregated_metrics.QueryFP,
        concordance,
        ci_lower,
        ci_upper,
    )


def process_variant_metrics(
    file_paths: Sequence[str], 
    data_type: str
) -> dict[tuple[str, str], tuple[int, int, int, float, float, float]]:
    """Process variant metrics and compute confidence intervals.

    Args:
        file_paths: Sequence of file paths to process
        data_type: Specifies whether the files are 'happy' or 'wittyer' data

    Returns:
        Dictionary mapping (variant_type, filter) to metrics tuple:
            truth_tp: Number of true positives in truth set
            truth_fn: Number of false negatives
            query_fp: Number of false positives
            concordance: Concordance rate between 0 and 1
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
    """
    metrics = load_data_from_files(file_paths, data_type=data_type)
    return compute_concordance_and_ci(metrics)
