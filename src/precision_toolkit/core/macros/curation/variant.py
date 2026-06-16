"""Shared functionality for manual variant curation scripts."""

import logging

import pandas as pd

from precision_toolkit.core.constants import (
    DEFAULT_CI_LEVEL,
    DEFAULT_DECIMALS,
    DiagnosticMetricType,
    NameMapper,
)
from precision_toolkit.core.metrics.variant import (
    ConcordanceMetrics,
    ConcordanceTPMethod,
    F1ScoreMetrics,
    PrecisionMetrics,
    SensitivityMetrics,
    VariantCallMetrics,
)
from precision_toolkit.core.statistics.proportion import (
    ProportionConfidenceIntervalMethod,
)
from precision_toolkit.render.diagnostic_metrics import (
    export_diagnostic_metrics_to_csv,
    export_diagnostic_metrics_to_markdown,
    export_diagnostic_metrics_to_word,
)


def validate_curation_format(curation: str, valid_metrics: list[str]) -> bool:
    """Validate manual curation input format.

    Args:
        curation: Manual curation input in format type:filter:metric:count
        valid_metrics: List of valid metrics for the specific analysis

    Returns:
        True if format is valid

    Raises:
        ValueError: If format is invalid
    """
    try:
        _, _, metric, count = curation.split(":")
        float(count)
        if metric.lower() not in [m.lower() for m in valid_metrics]:
            raise ValueError(
                f"Invalid metric: {metric}. Must be one of: {valid_metrics}"
            )
        return True
    except ValueError as e:
        raise ValueError(f"Invalid curation format: {e}")


def update_metrics(
    df: pd.DataFrame,
    curation: str,
    metric_type: DiagnosticMetricType,
    tp_method: ConcordanceTPMethod,
    ci_method: ProportionConfidenceIntervalMethod = (
        ProportionConfidenceIntervalMethod.WILSON
    ),
    ci_level: float = DEFAULT_CI_LEVEL,
) -> pd.DataFrame:
    """Update metrics in the DataFrame based on manual curation.

    Args:
        df: DataFrame containing metrics
        curation: Manual curation input in format type:filter:metric:count
        metric_type: Metric to use for calculations (e.g., "sensitivity")
        tp_method: TP method for concordance (only used for ConcordanceMetrics)
        ci_method: Method for calculating confidence intervals
        ci_level: Confidence level for confidence intervals

    Returns:
        Updated DataFrame
    """
    variant_type, filter_type, metric_str, value_str = curation.split(":")
    value = (
        float(value_str)
        if metric_type == DiagnosticMetricType.F1_SCORE
        else int(value_str)
    )

    try:
        metric_full = (
            metric_str.capitalize()
            if metric_type == DiagnosticMetricType.F1_SCORE
            else NameMapper.get_full_name(metric_str.upper())
        )
    except ValueError as e:
        logging.error(e)
        raise

    mask = (df["Variant Type"] == variant_type) & (df["Variant Filter"] == filter_type)
    df.loc[mask, metric_full] = value

    # Create metrics object based on the metric class
    metrics: VariantCallMetrics
    metric_value: float
    ci_lower: float | None = None
    ci_upper: float | None = None

    if metric_type == DiagnosticMetricType.SENSITIVITY:
        metrics = VariantCallMetrics(
            VariantType=variant_type,
            VariantCallFilter=filter_type,
            TruthTotal=df.loc[mask, "True Positive"].sum()
            + df.loc[mask, "False Negative"].sum(),
            TruthTP=df.loc[mask, "True Positive"].sum(),
            TruthFN=df.loc[mask, "False Negative"].sum(),
            QueryTotal=0,
            QueryTP=0,
            QueryFP=0,
        )
        sensitivity_analysis = SensitivityMetrics(metrics)
        metric_value = sensitivity_analysis.sensitivity
        ci_lower, ci_upper = sensitivity_analysis.confidence_interval(
            method=ci_method,
            ci_level=ci_level,
        )
    elif metric_type == DiagnosticMetricType.PRECISION:
        metrics = VariantCallMetrics(
            VariantType=variant_type,
            VariantCallFilter=filter_type,
            TruthTotal=0,
            TruthTP=0,
            TruthFN=0,
            QueryTotal=df.loc[mask, "True Positive"].sum()
            + df.loc[mask, "False Positive"].sum(),
            QueryTP=df.loc[mask, "True Positive"].sum(),
            QueryFP=df.loc[mask, "False Positive"].sum(),
        )
        precision_analysis = PrecisionMetrics(metrics)
        metric_value = precision_analysis.precision
        ci_lower, ci_upper = precision_analysis.confidence_interval(
            method=ci_method,
            ci_level=ci_level,
        )
    elif metric_type == DiagnosticMetricType.CONCORDANCE:
        metrics = VariantCallMetrics(
            VariantType=variant_type,
            VariantCallFilter=filter_type,
            TruthTotal=df.loc[mask, "True Positive"].sum()
            + df.loc[mask, "False Negative"].sum(),
            TruthTP=df.loc[mask, "True Positive"].sum(),
            TruthFN=df.loc[mask, "False Negative"].sum(),
            QueryTotal=df.loc[mask, "True Positive"].sum()
            + df.loc[mask, "False Positive"].sum(),
            QueryTP=df.loc[mask, "True Positive"].sum(),
            QueryFP=df.loc[mask, "False Positive"].sum(),
        )
        concordance_analysis = ConcordanceMetrics(metrics, tp_method)
        metric_value = concordance_analysis.concordance
        ci_lower, ci_upper = concordance_analysis.confidence_interval(
            method=ci_method,
            ci_level=ci_level,
        )
    elif metric_type == DiagnosticMetricType.F1_SCORE:
        sensitivity = df.loc[mask, "Sensitivity"].sum()
        precision = df.loc[mask, "Precision"].sum()
        f1_score_analysis = F1ScoreMetrics(sensitivity=sensitivity, precision=precision)
        metric_value = f1_score_analysis.f1_score
        ci_lower = ci_upper = None

    # Update DataFrame with new metric value
    metric_name = (
        "F1 Score"
        if metric_type == DiagnosticMetricType.F1_SCORE
        else metric_type.value.capitalize()
    )
    df.loc[mask, metric_name] = metric_value

    # Update CI values if they exist
    if ci_lower is not None and ci_upper is not None:
        df.loc[mask, "CI Lower"] = ci_lower
        df.loc[mask, "CI Upper"] = ci_upper

    return df


def export_curation_results(
    df: pd.DataFrame,
    output_prefix: str,
    metric_type: DiagnosticMetricType,
    decimals: int = DEFAULT_DECIMALS,
) -> None:
    """Export results to CSV, Markdown, and Word formats.

    Args:
        df: DataFrame containing results
        output_prefix: Prefix for output files
        metric_type: Type of metric (e.g. "sensitivity")
        summary_text: Summary text for the report
    """
    metric_name = "F1 Score" if metric_type == "f1_score" else metric_type
    summary_text = f"Manually curated {metric_name.capitalize()} summary"
    export_diagnostic_metrics_to_csv(df, f"{output_prefix}.csv")
    export_diagnostic_metrics_to_markdown(
        [df],
        f"{output_prefix}.md",
        metric_types=[metric_type],
        headings=f"Manually Curated {metric_name.capitalize()}",
        summaries=summary_text,
        decimals=decimals,
    )
    export_diagnostic_metrics_to_word(
        [df],
        f"{output_prefix}.docx",
        metric_types=[metric_type],
        headings=f"Manually Curated {metric_name.capitalize()}",
        summaries=summary_text,
        decimals=decimals,
    )
