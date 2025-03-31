"""Shared functionality for manual variant curation scripts."""

import logging
from typing import Literal

import pandas as pd

from clinical_tools.core.constants import DEFAULT_DECIMALS, NameMapper
from clinical_tools.core.metrics.variant import (
    ConcordanceMetrics,
    F1ScoreMetrics,
    PrecisionMetrics,
    SensitivityMetrics,
    VariantCallMetrics,
)
from clinical_tools.render.diagnostic_metrics import (
    export_diagnostic_metrics_to_csv,
    export_diagnostic_metrics_to_markdown,
    export_diagnostic_metrics_to_word,
)


def validate_curation_format(curation: str, valid_metrics: list[str]) -> bool:
    """
    Validate manual curation input format.

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
        if metric not in valid_metrics:
            raise ValueError(
                f"Invalid metric: {metric}. Must be one of: {valid_metrics}"
            )
        return True
    except ValueError as e:
        raise ValueError(f"Invalid curation format: {e}")


def update_metrics(
    df: pd.DataFrame, curation: str, metric_class: type, tp_method: str | None = None
) -> pd.DataFrame:
    """
    Update metrics in the DataFrame based on manual curation.

    Args:
        df: DataFrame containing metrics
        curation: Manual curation input in format type:filter:metric:count
        metric_class: Metric class to use for calculations (e.g., SensitivityMetrics)
        tp_method: TP method for concordance (only used for ConcordanceMetrics)

    Returns:
        Updated DataFrame
    """
    variant_type, filter_type, metric, value_str = curation.split(":")
    value = float(value_str) if metric_class == F1ScoreMetrics else int(value_str)

    try:
        metric_full = (
            metric.capitalize()
            if metric_class == F1ScoreMetrics
            else NameMapper.get_full_name(metric)
        )
    except ValueError as e:
        logging.error(e)
        raise

    mask = (df["Variant Type"] == variant_type) & (df["Variant Filter"] == filter_type)
    df.loc[mask, metric_full] = value

    # Create metrics object based on the metric class
    if metric_class == SensitivityMetrics:
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
    elif metric_class == PrecisionMetrics:
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
    elif metric_class == ConcordanceMetrics:
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
    elif metric_class == F1ScoreMetrics:
        sensitivity = df.loc[mask, "Sensitivity"].sum()
        precision = df.loc[mask, "Precision"].sum()
        metric_value = F1ScoreMetrics(sensitivity, precision).f1_score

    # Calculate metrics
    if metric_class != F1ScoreMetrics:
        analysis = (
            metric_class(metrics)
            if tp_method is None
            else metric_class(metrics, tp_method)
        )
        metric_value = getattr(
            analysis, metric_class.__name__.lower().replace("metrics", "")
        )
        ci_lower, ci_upper = analysis.confidence_interval()
        df.loc[mask, "CI Lower"] = ci_lower
        df.loc[mask, "CI Upper"] = ci_upper

    # Update DataFrame
    metric_name = (
        "F1 Score"
        if metric_class.__name__ == "F1ScoreMetrics"
        else metric_class.__name__.lower().replace("metrics", "").capitalize()
    )
    df.loc[mask, metric_name] = metric_value

    return df


def export_curation_results(
    df: pd.DataFrame,
    output_prefix: str,
    metric_type: Literal["concordance", "sensitivity", "precision", "f1_score"],
    decimals: int = DEFAULT_DECIMALS,
) -> None:
    """
    Export results to CSV, Markdown, and Word formats.

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
