"""Diagnostic metrics rendering."""

import typing
from pathlib import Path

import pandas as pd

from clinical_tools.core.constants import DEFAULT_DECIMALS, DiagnosticMetricType
from clinical_tools.core.format import format_percentage
from clinical_tools.core.helpers import assemble_exports
from clinical_tools.core.writers.markdown import populate_markdown, save_markdown
from clinical_tools.core.writers.table import pandas_to_csv
from clinical_tools.core.writers.word import (
    initiate_word_document,
    pandas_to_word,
    save_word_document,
)


def generate_diagnostic_metrics_table(
    results: dict[tuple[str, str], tuple], metric_type: DiagnosticMetricType
) -> pd.DataFrame:
    """Generate diagnostic metrics summary.

    Args:
        results: Dictionary where keys are tuples of (variant_type, variant_filter)
            and values are tuples of metrics
        metric_type: Type of metric being processed (DiagnosticMetricType)

    Returns:
        DataFrame of diagnostic metrics, sorted by Variant Type and Filter
    """
    if metric_type == "concordance":
        columns = [
            "Variant Type",
            "Variant Filter",
            "True Positive",
            "False Negative",
            "False Positive",
            "Concordance",
            "CI Lower",
            "CI Upper",
        ]
        data = [
            {
                "Variant Type": variant_type,
                "Variant Filter": variant_filter,
                "True Positive": true_positive,
                "False Negative": false_negative,
                "False Positive": false_positive,
                "Concordance": concordance,
                "CI Lower": ci_lower,
                "CI Upper": ci_upper,
            }
            for (variant_type, variant_filter), (
                true_positive,
                false_negative,
                false_positive,
                concordance,
                ci_lower,
                ci_upper,
            ) in results.items()
        ]
    elif metric_type == "sensitivity":
        columns = [
            "Variant Type",
            "Variant Filter",
            "True Positive",
            "False Negative",
            "Sensitivity",
            "CI Lower",
            "CI Upper",
        ]
        data = [
            {
                "Variant Type": variant_type,
                "Variant Filter": variant_filter,
                "True Positive": true_positive,
                "False Negative": false_negative,
                "Sensitivity": sensitivity,
                "CI Lower": ci_lower,
                "CI Upper": ci_upper,
            }
            for (variant_type, variant_filter), (
                true_positive,
                false_negative,
                sensitivity,
                ci_lower,
                ci_upper,
            ) in results.items()
        ]
    elif metric_type == "precision":
        columns = [
            "Variant Type",
            "Variant Filter",
            "True Positive",
            "False Positive",
            "Precision",
            "CI Lower",
            "CI Upper",
        ]
        data = [
            {
                "Variant Type": variant_type,
                "Variant Filter": variant_filter,
                "True Positive": true_positive,
                "False Positive": false_positive,
                "Precision": precision,
                "CI Lower": ci_lower,
                "CI Upper": ci_upper,
            }
            for (variant_type, variant_filter), (
                true_positive,
                false_positive,
                precision,
                ci_lower,
                ci_upper,
            ) in results.items()
        ]
    elif metric_type == "f1_score":
        columns = [
            "Variant Type",
            "Variant Filter",
            "Sensitivity",
            "Precision",
            "F1 Score",
        ]
        data = [
            {
                "Variant Type": variant_type,
                "Variant Filter": variant_filter,
                "Sensitivity": sensitivity,
                "Precision": precision,
                "F1 Score": f1_score,
            }
            for (variant_type, variant_filter), (
                sensitivity,
                precision,
                f1_score,
            ) in results.items()
        ]
    else:
        raise ValueError(f"Unsupported metric type: {metric_type}")

    df = pd.DataFrame(data, columns=columns)
    return df.sort_values(by=["Variant Type", "Variant Filter"])


def format_diagnostic_metrics_table(
    df: pd.DataFrame,
    metric_type: DiagnosticMetricType,
    decimals: int = DEFAULT_DECIMALS,
) -> pd.DataFrame:
    """Format the metric and confidence interval columns as percentages.

    Args:
        df: The metrics DataFrame to format
        metric_type: Type of metric being processed (DiagnosticMetricType)
        decimals: Number of decimal places for percentages

    Returns:
        New DataFrame with formatted columns
    """
    formatted_df = df.copy()
    metric_col = "F1 Score" if metric_type == "f1_score" else metric_type.capitalize()
    # Only format CI columns if they exist
    cols_to_format = [metric_col]
    if metric_type == "f1_score":
        cols_to_format.extend(["Sensitivity", "Precision"])
    if "CI Lower" in df.columns and "CI Upper" in df.columns:
        cols_to_format.extend(["CI Lower", "CI Upper"])
    for col in cols_to_format:
        formatted_df[col] = formatted_df[col].apply(
            format_percentage, decimals=decimals
        )
    return formatted_df


def export_diagnostic_metrics_to_csv(df: pd.DataFrame, output_file: str | Path) -> None:
    """Export a diagnostic metrics DataFrame to a CSV file."""
    pandas_to_csv(df, output_file)


def export_diagnostic_metrics_to_markdown(
    dfs: list[pd.DataFrame] | pd.DataFrame,
    output_file: str | Path,
    metric_types: list[DiagnosticMetricType] | DiagnosticMetricType,
    headings: list[str] | str | None = None,
    summaries: list[str] | str | None = None,
    decimals: int = DEFAULT_DECIMALS,
) -> None:
    """Export one or more diagnostic metrics DataFrames to Markdown file.

    Args:
        dfs: Single DataFrame or list of DataFrames to export
        output_file: Path to save the Markdown file
        metric_types: Single metric type or list of metric types matching the DataFrames
        headings: Optional heading(s) to add to the file. If multiple DataFrames,
        should be a list of headings matching DataFrame count.
        summaries: Optional summary(s) to add before table(s). If multiple
        DataFrames, should be a list of summaries matching DataFrame count.
        decimals: Number of decimal places for percentages

    """
    dfs, headings, summaries = assemble_exports(dfs, headings, summaries)
    if isinstance(metric_types, str):
        metric_types = [metric_types] * len(dfs)
    elif len(metric_types) != len(dfs):
        raise ValueError("Number of metric types must match number of DataFrames")

    # Process each DataFrame and collect markdown content
    all_content = []
    for i, df in enumerate(dfs):
        formatted_df = format_diagnostic_metrics_table(
            typing.cast(pd.DataFrame, df),
            metric_types[i],
            decimals,
        )
        heading = headings[i] if headings else None
        summary = summaries[i] if summaries else None
        content = populate_markdown(formatted_df, heading, summary)
        all_content.append(content)

    # Combine all content and save to file
    final_content = "\n\n".join(all_content)
    save_markdown(final_content, output_file)


def export_diagnostic_metrics_to_word(
    dfs: list[pd.DataFrame] | pd.DataFrame,
    output_file: str | Path,
    metric_types: list[DiagnosticMetricType] | DiagnosticMetricType,
    headings: list[str] | str | None = None,
    summaries: list[str] | str | None = None,
    decimals: int = DEFAULT_DECIMALS,
) -> None:
    """Export one or more diagnostic metrics DataFrames to Word file.

    Args:
        dfs: Single DataFrame or list of DataFrames to export
        output_file: Path to save the Word file
        metric_types: Single metric type or list of metric types matching the DataFrames
        headings: Optional heading(s) to add to the file. If multiple DataFrames,
        should be a list of headings matching DataFrame count.
        summaries: Optional summary(s) to add before table(s). If multiple
        DataFrames, should be a list of summaries matching DataFrame count.
        decimals: Number of decimal places for percentages

    """
    dfs, headings, summaries = assemble_exports(dfs, headings, summaries)
    if isinstance(metric_types, str):
        metric_types = [metric_types] * len(dfs)
    elif len(metric_types) != len(dfs):
        raise ValueError("Number of metric types must match number of DataFrames")

    # Initiate Word document
    doc = initiate_word_document()

    # Process each DataFrame and add to Word document
    for i, df in enumerate(dfs):
        formatted_df = format_diagnostic_metrics_table(
            typing.cast(pd.DataFrame, df),
            metric_types[i],
            decimals,
        )
        heading = headings[i] if headings else None
        summary = summaries[i] if summaries else None
        pandas_to_word(formatted_df, doc, heading, summary)

    # Save final Word document
    save_word_document(output_file, doc)
