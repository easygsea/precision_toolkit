import pandas as pd
from pathlib import Path
from clinical_tools.core.format import format_percentage
from clinical_tools.core.writers.csv import pandas_to_csv
from clinical_tools.core.writers.markdown import populate_markdown, save_markdown
from clinical_tools.core.writers.word import (
    pandas_to_word,
    initiate_word_document,
    save_word_document,
)
from clinical_tools.analysis.compute_variant_metrics import process_variant_metrics


def generate_concordance_table(
    results: dict[tuple[str, str], tuple[int, int, int, float, float, float]]
) -> pd.DataFrame:
    """
    Generate a pandas DataFrame for variant concordance summary.

    Args:
        results: Dictionary where keys are tuples of (variant_type, variant_filter) 
            and values are tuples of metrics (true_positive, false_negative, 
            false_positive, concordance, ci_lower, ci_upper)

    Returns:
        DataFrame summarizing variant concordance
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
    return pd.DataFrame(data)


def format_concordance_table(df: pd.DataFrame) -> pd.DataFrame:
    """Format the Concordance, CI Lower, and CI Upper columns as percentages.

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
    """Export concordance DataFrame to CSV file.

    Args:
        df: The concordance DataFrame
        output_file: Path to save the CSV file
    """
    pandas_to_csv(df, output_file)


def export_concordance_to_markdown(
    df: pd.DataFrame,
    output_file: str | Path,
    heading: str | None = None,
    summary: str | None = None
) -> None:
    """Export concordance DataFrame to Markdown file.

    Args:
        df: The concordance DataFrame
        output_file: Path to save the Markdown file
        heading: Optional heading to add to the file
        summary: Optional summary to add before the table
    """
    formatted_df = format_concordance_table(df)
    content = populate_markdown(formatted_df, heading, summary)
    save_markdown(content, output_file)


def export_concordance_to_word(
    df: pd.DataFrame,
    output_file: str | Path,
    heading: str | None = None,
    summary: str | None = None
) -> None:
    """Export concordance DataFrame to Word file.

    Args:
        df: The concordance DataFrame
        output_file: Path to save the Word file
        heading: Optional heading to add to the file
        summary: Optional summary to add before the table
    """
    formatted_df = format_concordance_table(df)
    doc = initiate_word_document()
    pandas_to_word(doc, formatted_df, heading, summary)
    save_word_document(doc, output_file)
