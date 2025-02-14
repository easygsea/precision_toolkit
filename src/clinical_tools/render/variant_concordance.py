from pathlib import Path

import pandas as pd

from clinical_tools.analysis.compute_variant_metrics import process_variant_metrics
from clinical_tools.core.format import format_percentage
from clinical_tools.core.helpers import assemble_exports
from clinical_tools.core.writers.csv import pandas_to_csv
from clinical_tools.core.writers.markdown import populate_markdown, save_markdown
from clinical_tools.core.writers.word import (
    initiate_word_document,
    pandas_to_word,
    save_word_document,
)


def generate_concordance_table(
    results: dict[tuple[str, str], tuple[int, int, int, float, float, float]],
) -> pd.DataFrame:
    """
    Generate a pandas DataFrame for variant concordance summary.

    Args:
        results: Dictionary where keys are tuples of (variant_type, variant_filter)
            and values are tuples of metrics (true_positive, false_negative,
            false_positive, concordance, ci_lower, ci_upper)

    Returns:
        DataFrame summarizing variant concordance, sorted by Variant Type then Variant Filter
    """
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
    df = pd.DataFrame(data)
    return df.sort_values(by=["Variant Type", "Variant Filter"])


def format_concordance_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format the Concordance, CI Lower, and CI Upper columns as percentages.

    Args:
        df: The concordance DataFrame to format

    Returns:
        New DataFrame with formatted columns
    """
    formatted_df = df.copy()
    for col in ["Concordance", "CI Lower", "CI Upper"]:
        formatted_df[col] = formatted_df[col].apply(format_percentage)
    return formatted_df


def export_concordance_to_csv(df: pd.DataFrame, output_file: str | Path) -> None:
    """
    Export concordance DataFrame to CSV file.

    Args:
        df: The concordance DataFrame
        output_file: Path to save the CSV file
    """
    pandas_to_csv(df, output_file)


def export_concordance_to_markdown(
    dfs: list[pd.DataFrame] | pd.DataFrame,
    output_file: str | Path,
    headings: list[str] | str | None = None,
    summaries: list[str] | str | None = None,
) -> None:
    """
    Export one or more concordance DataFrames to Markdown file.

    Args:
        dfs: Single DataFrame or list of DataFrames to export
        output_file: Path to save the Markdown file
        headings: Optional heading(s) to add to the file. If multiple DataFrames,
            should be a list of headings matching the number of DataFrames.
        summaries: Optional summary(s) to add before the table(s). If multiple DataFrames,
            should be a list of summaries matching the number of DataFrames.
    """
    dfs, headings, summaries = assemble_exports(dfs, headings, summaries)

    # Process each DataFrame and collect markdown content
    all_content = []
    for i, df in enumerate(dfs):
        formatted_df = format_concordance_table(df)
        heading = headings[i] if headings else None
        summary = summaries[i] if summaries else None
        content = populate_markdown(formatted_df, heading, summary)
        all_content.append(content)

    # Combine all content and save to file
    final_content = "\n\n".join(all_content)
    save_markdown(final_content, output_file)


def export_concordance_to_word(
    dfs: list[pd.DataFrame] | pd.DataFrame,
    output_file: str | Path,
    headings: list[str] | str | None = None,
    summaries: list[str] | str | None = None,
) -> None:
    """
    Export one or more concordance DataFrames to Word file.

    Args:
        dfs: Single DataFrame or list of DataFrames to export
        output_file: Path to save the Word file
        headings: Optional heading(s) to add to the file. If multiple DataFrames,
            should be a list of headings matching the number of DataFrames.
        summaries: Optional summary(s) to add before the table(s). If multiple DataFrames,
            should be a list of summaries matching the number of DataFrames.
    """
    dfs, headings, summaries = assemble_exports(dfs, headings, summaries)

    # Initiate Word document
    doc = initiate_word_document()

    # Process each DataFrame and add to Word document
    for i, df in enumerate(dfs):
        formatted_df = format_concordance_table(df)
        heading = headings[i] if headings else None
        summary = summaries[i] if summaries else None
        pandas_to_word(doc, formatted_df, heading, summary)

    # Save final Word document
    save_word_document(doc, output_file)
