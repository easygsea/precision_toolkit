"""Compute diagnostic metrics from VCF comparisons."""

from collections import defaultdict
from collections.abc import Sequence

from clinical_tools.core.constants import (
    DEFAULT_CI_LEVEL,
    DiagnosticMetricType,
    VariantConcordanceEngine,
)
from clinical_tools.core.metrics.variant import (
    ConcordanceMetrics,
    ConcordanceTPMethod,
    F1ScoreMetrics,
    PrecisionMetrics,
    SensitivityMetrics,
    VariantCallMetrics,
)
from clinical_tools.core.parsers.happy import HappyDataParser
from clinical_tools.core.parsers.sompy import SompyDataParser
from clinical_tools.core.parsers.wittyer import WittyerDataParser
from clinical_tools.core.statistics.proportion import (
    ProportionConfidenceIntervalMethod,
)


def load_data_from_files(
    files: Sequence[str], data_type: VariantConcordanceEngine
) -> list[VariantCallMetrics]:
    """Load data from files based on the specified data type.

    Args:
        files: Sequence of paths to the files to be loaded
        data_type: Type of data to load ('happy', 'sompy', or 'wittyer')

    Returns:
        Sequence of parsed metrics

    Raises:
        ValueError: If no files provided or invalid data_type
    """
    if not files:
        raise ValueError("No files provided")

    if data_type == VariantConcordanceEngine.HAPPY:
        parser = HappyDataParser.process_hap_py_output
    elif data_type == VariantConcordanceEngine.SOMPY:
        parser = SompyDataParser.process_sompy_output
    elif data_type == VariantConcordanceEngine.WITTYER:
        parser = WittyerDataParser.process_witty_er_output
    else:
        raise ValueError(
            f"Unsupported data_type: {data_type}. Must be one of: happy, sompy, wittyer"
        )

    all_metrics: list[VariantCallMetrics] = []
    for file_path in files:
        try:
            all_metrics.extend(parser(file_path))
        except Exception as e:
            raise RuntimeError(f"Error processing file {file_path}: {str(e)}")

    return all_metrics


def compute_concordance_and_ci(
    metrics: list[VariantCallMetrics],
    tp_method: ConcordanceTPMethod,
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float = DEFAULT_CI_LEVEL,
) -> dict[tuple[str, str], tuple[int, int, int, float, float, float]]:
    """Compute concordance and confidence intervals grouped by variant type and filter.

    Args:
        metrics: Sequence of parsed metrics across samples
        tp_method: Method for selecting TP in concordance
        ci_method: Statistical method for confidence interval calculation
        ci_level: Confidence level for confidence intervals (default: DEFAULT_CI_LEVEL)

    Returns:
        Dictionary mapping (variant_type, filter) to metrics tuple:
            selected_tp: Number of true positives
            truth_fn: Number of false negatives
            query_fp: Number of false positives
            concordance: Concordance rate between 0 and 1
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
    """
    grouped_metrics = defaultdict(list)
    for metric in metrics:
        key = (metric.VariantType, metric.VariantCallFilter)
        grouped_metrics[key].append(metric)

    return {
        key: _compute_concordance_and_ci_for_group(
            group, tp_method, ci_method, ci_level
        )
        for key, group in grouped_metrics.items()
    }


def _compute_concordance_and_ci_for_group(
    group: list[VariantCallMetrics],
    tp_method: ConcordanceTPMethod,
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float = DEFAULT_CI_LEVEL,
) -> tuple[int, int, int, float, float, float]:
    """Calculate concordance and confidence intervals for a group of variants.

    Helper function for compute_concordance_and_ci that processes
    a single group of variants with the same type and filter.

    Args:
        group: List of variant metrics to aggregate, all with same type and filter
        tp_method: Method for selecting TP in concordance
        ci_method: Statistical method for confidence interval calculation
        ci_level: Confidence level for confidence intervals (default: DEFAULT_CI_LEVEL)

    Returns:
        Tuple of metrics:
            selected_tp: Number of true positives
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

    analysis = ConcordanceMetrics(aggregated_metrics, tp_method)
    concordance = analysis.concordance
    ci_lower, ci_upper = analysis.confidence_interval(ci_method, ci_level)

    return (
        analysis._ci_successes,
        aggregated_metrics.TruthFN,
        aggregated_metrics.QueryFP,
        concordance,
        ci_lower,
        ci_upper,
    )


def compute_sensitivity_and_ci(
    metrics: list[VariantCallMetrics],
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float = DEFAULT_CI_LEVEL,
) -> dict[tuple[str, str], tuple[int, int, float, float, float]]:
    """Compute sensitivity and confidence intervals grouped by variant type and filter.

    Args:
        metrics: Sequence of parsed metrics across samples
        ci_method: Statistical method for confidence interval calculation
        ci_level: Confidence level for confidence intervals (default: DEFAULT_CI_LEVEL)

    Returns:
        Dictionary mapping (variant_type, filter) to metrics tuple:
            truth_tp: Number of true positives
            truth_fn: Number of false negatives
            sensitivity: Sensitivity rate between 0 and 1
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
    """
    grouped_metrics = defaultdict(list)
    for metric in metrics:
        key = (metric.VariantType, metric.VariantCallFilter)
        grouped_metrics[key].append(metric)

    return {
        key: _compute_sensitivity_and_ci_for_group(group, ci_method, ci_level)
        for key, group in grouped_metrics.items()
    }


def _compute_sensitivity_and_ci_for_group(
    group: list[VariantCallMetrics],
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float = DEFAULT_CI_LEVEL,
) -> tuple[int, int, float, float, float]:
    """Calculate sensitivity and confidence intervals for a group of variants.

    Args:
        group: List of variant metrics to aggregate, all with same type and filter
        ci_method: Statistical method for confidence interval calculation
        ci_level: Confidence level for confidence intervals (default: DEFAULT_CI_LEVEL)

    Returns:
        Tuple of metrics:
            truth_tp: Number of true positives
            truth_fn: Number of false negatives
            sensitivity: Sensitivity rate between 0 and 1
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
    """
    total_truth_tp = sum(metric.TruthTP for metric in group)
    total_truth_fn = sum(metric.TruthFN for metric in group)

    aggregated_metrics = VariantCallMetrics(
        VariantType=group[0].VariantType,
        VariantCallFilter=group[0].VariantCallFilter,
        TruthTotal=total_truth_tp + total_truth_fn,
        TruthTP=total_truth_tp,
        TruthFN=total_truth_fn,
        QueryTotal=0,  # Not used for sensitivity
        QueryTP=0,  # Not used for sensitivity
        QueryFP=0,  # Not used for sensitivity
    )

    analysis = SensitivityMetrics(aggregated_metrics)
    sensitivity = analysis.sensitivity
    ci_lower, ci_upper = analysis.confidence_interval(ci_method, ci_level)

    return (total_truth_tp, total_truth_fn, sensitivity, ci_lower, ci_upper)


def compute_precision_and_ci(
    metrics: list[VariantCallMetrics],
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float = DEFAULT_CI_LEVEL,
) -> dict[tuple[str, str], tuple[int, int, float, float, float]]:
    """Compute precision and confidence intervals grouped by variant type and filter.

    Args:
        metrics: Sequence of parsed metrics across samples
        ci_method: Statistical method for confidence interval calculation
        ci_level: Confidence level for confidence intervals (default: DEFAULT_CI_LEVEL)

    Returns:
        Dictionary mapping (variant_type, filter) to metrics tuple:
            query_tp: Number of true positives
            query_fp: Number of false positives
            precision: Precision rate between 0 and 1
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
    """
    grouped_metrics = defaultdict(list)
    for metric in metrics:
        key = (metric.VariantType, metric.VariantCallFilter)
        grouped_metrics[key].append(metric)

    return {
        key: _compute_precision_and_ci_for_group(group, ci_method, ci_level)
        for key, group in grouped_metrics.items()
    }


def _compute_precision_and_ci_for_group(
    group: list[VariantCallMetrics],
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float = DEFAULT_CI_LEVEL,
) -> tuple[int, int, float, float, float]:
    """Calculate precision and confidence intervals for a group of variants.

    Args:
        group: List of variant metrics to aggregate, all with same type and filter
        ci_method: Statistical method for confidence interval calculation
        ci_level: Confidence level for confidence intervals (default: DEFAULT_CI_LEVEL)

    Returns:
        Tuple of metrics:
            query_tp: Number of true positives
            query_fp: Number of false positives
            precision: Precision rate between 0 and 1
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
    """
    total_query_tp = sum(metric.QueryTP for metric in group)
    total_query_fp = sum(metric.QueryFP for metric in group)

    aggregated_metrics = VariantCallMetrics(
        VariantType=group[0].VariantType,
        VariantCallFilter=group[0].VariantCallFilter,
        TruthTotal=0,  # Not used for precision
        TruthTP=0,  # Not used for precision
        TruthFN=0,  # Not used for precision
        QueryTotal=total_query_tp + total_query_fp,
        QueryTP=total_query_tp,
        QueryFP=total_query_fp,
    )

    analysis = PrecisionMetrics(aggregated_metrics)
    precision = analysis.precision
    ci_lower, ci_upper = analysis.confidence_interval(ci_method, ci_level)

    return (total_query_tp, total_query_fp, precision, ci_lower, ci_upper)


def compute_f1_score(
    metrics: list[VariantCallMetrics],
    ci_method: ProportionConfidenceIntervalMethod,
) -> dict[tuple[str, str], tuple[float, float, float]]:
    """Calculate F1 score from sensitivity and precision for grouped metrics.

    Args:
        metrics: Sequence of parsed metrics across samples
        ci_method: Statistical method for confidence interval calculation

    Returns:
        Dictionary mapping (variant_type, filter) to tuple of:
            sensitivity: Sensitivity value between 0 and 1
            precision: Precision value between 0 and 1
            f1_score: F1 score value between 0 and 1
    """
    precision_results = compute_precision_and_ci(metrics, ci_method)
    sensitivity_results = compute_sensitivity_and_ci(metrics, ci_method)

    f1_scores = {}
    for key in precision_results.keys():
        sensitivity = sensitivity_results[key][2]
        precision = precision_results[key][2]
        f1_metrics = F1ScoreMetrics(sensitivity=sensitivity, precision=precision)
        f1_scores[key] = (sensitivity, precision, f1_metrics.f1_score)

    return f1_scores


def process_diagnostic_metrics(
    file_paths: Sequence[str],
    data_type: VariantConcordanceEngine,
    tp_method: ConcordanceTPMethod,
    metrics: list[DiagnosticMetricType],
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float = DEFAULT_CI_LEVEL,
) -> dict[str, dict[tuple[str, str], tuple]]:
    """Process VCF comparison results and compute diagnostic metrics.

    Args:
        file_paths: Sequence of file paths to process
        data_type: Specifies VariantConcordanceEngine
        tp_method: Method for selecting TP in concordance (only used for concordance)
        metrics: Sequence of metrics to compute
        ci_method: Statistical method for confidence interval calculation
        ci_level: Confidence level for confidence intervals (default: DEFAULT_CI_LEVEL)

    Returns:
        Dict mapping metric name to results dict:
            concordance: Dict mapping (variant_type, filter) to (tp, fn, fp,
                metric, ci_lower, ci_upper)
            sensitivity: Dict mapping (variant_type, filter) to (tp, fn,
                metric, ci_lower, ci_upper)
            precision: Dict mapping (variant_type, filter) to (tp, fp,
                metric, ci_lower, ci_upper)
            f1_score: Dict mapping (variant_type, filter) to (f1_score)
    """
    metrics_data = load_data_from_files(file_paths, data_type=data_type)

    result: dict[str, dict[tuple[str, str], tuple]] = {}
    grouped_metrics = defaultdict(list)
    for metric in metrics_data:
        key = (metric.VariantType, metric.VariantCallFilter)
        grouped_metrics[key].append(metric)

    for metric_type in metrics:
        if metric_type == "concordance":
            result["concordance"] = compute_concordance_and_ci(
                metrics_data, tp_method, ci_method, ci_level
            )
        elif metric_type == "sensitivity":
            result["sensitivity"] = compute_sensitivity_and_ci(
                metrics_data, ci_method, ci_level
            )
        elif metric_type == "precision":
            result["precision"] = compute_precision_and_ci(
                metrics_data, ci_method, ci_level
            )
        elif metric_type == "f1_score":
            result["f1_score"] = compute_f1_score(metrics_data, ci_method)

    return result
