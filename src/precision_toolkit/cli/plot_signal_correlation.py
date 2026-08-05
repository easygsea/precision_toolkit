r"""
Generate a scatter plot from paired truth and query signal files.

Each signal file should have the following columns:
- CHROM
- POS
- REF
- ALT
- SIGNAL_NAME

The script will generate a scatter plot with an optional pearson correlation
line. Example usage:

```
plot-signal-correlation
--truth-signal truth_vaf.tsv
--query-signal query_vaf.tsv
--output-filename vaf_correlation
--xlim 0 1
--ylim 0 1
--color-source run
--run-pattern "AB\\d{5}"
--show-regression
--color-palette tab10
```
"""

import argparse
import re
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from scipy import stats

from precision_toolkit.core.format import parse_percentage_and_float

CONSTANT_COLUMNS = ["CHROM", "POS", "REF", "ALT"]


def identify_raw_signal_columns(signal_df: pd.DataFrame) -> list[str]:
    """Identify signal column names from the raw signal DataFrame."""
    signal_cols = [
        col
        for col in signal_df.columns
        if col not in CONSTANT_COLUMNS and col != "FILTER"
    ]
    return signal_cols


def extract_signals(truth_signal_file: Path, query_signal_file: Path) -> pd.DataFrame:
    """Merge signals from truth and query files into one DataFrame."""
    truth_signal_df = pd.read_csv(truth_signal_file, sep="\t", header=0)
    query_signal_df = pd.read_csv(query_signal_file, sep="\t", header=0)

    truth_signal_cols = identify_raw_signal_columns(truth_signal_df)
    query_signal_cols = identify_raw_signal_columns(query_signal_df)

    # Auto convert % values to float
    for col in truth_signal_cols:
        truth_signal_df[col] = truth_signal_df[col].apply(parse_percentage_and_float)
    for col in query_signal_cols:
        query_signal_df[col] = query_signal_df[col].apply(parse_percentage_and_float)

    # Add suffixes to distinguish columns after merge
    truth_signal_df = truth_signal_df.rename(
        columns=lambda x: f"{x}_TRUTH" if x not in CONSTANT_COLUMNS else x
    )
    query_signal_df = query_signal_df.rename(
        columns=lambda x: f"{x}_QUERY" if x not in CONSTANT_COLUMNS else x
    )
    merged_df = pd.merge(
        truth_signal_df,
        query_signal_df,
        on=CONSTANT_COLUMNS,
    )

    return merged_df


def identify_signal_columns(signal_df: pd.DataFrame) -> tuple[str, str]:
    """
    Identify truth and query signal column names from the DataFrame.

    Args:
        signal_df: DataFrame with merged signals.

    Returns:
        Tuple of (truth_column_name, query_column_name).

    Raises:
        ValueError: If truth or query columns cannot be identified.
    """
    truth_cols = [
        col
        for col in signal_df.columns
        if col.endswith("_TRUTH") and not col.startswith("FILTER")
    ]
    query_cols = [
        col
        for col in signal_df.columns
        if col.endswith("_QUERY") and not col.startswith("FILTER")
    ]

    if not truth_cols or not query_cols:
        raise ValueError(
            "Could not identify signal columns. Expected columns with '_TRUTH' and "
            "'_QUERY' suffixes."
        )

    if len(truth_cols) > 1 or len(query_cols) > 1:
        raise ValueError(
            "Multiple signal columns found. Expected exactly one column with '_TRUTH' "
            "and one with '_QUERY' suffix."
        )

    return truth_cols[0], query_cols[0]


def calculate_correlation(signal_df: pd.DataFrame) -> tuple[float, float]:
    """Return Pearson correlation and p-value for merged signals."""
    if signal_df.empty:
        return 0.0, 1.0

    truth_col, query_col = identify_signal_columns(signal_df)

    corr_result = stats.pearsonr(signal_df[truth_col], signal_df[query_col])
    return float(corr_result.statistic), float(corr_result.pvalue)


def plot_signal_correlation(
    signal_df: pd.DataFrame,
    output_filename: str,
    show_regression: bool = False,
    title: str = "Signal Correlation",
    figsize: tuple[int, int] = (10, 10),
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    color_source: str = "",
    color_palette: str = "colorblind",
) -> None:
    """Scatter plot of merged signals with optional regression and correlation.

    Args:
        signal_df: Input DataFrame.
        output_filename: Output figure path.
        show_regression: If True, show regression line and Pearson stats.
        title: Plot title.
        figsize: Figure size (w, h).
        xlim: Optional tuple of (min, max) for x-axis range.
        ylim: Optional tuple of (min, max) for y-axis range.
        color_source: Color by 'FILTER_TRUTH', 'FILTER_QUERY', or 'RUN_ID' if provided.
        color_palette: Color scheme for plotting if provided.
    """
    # sort dataframe to ensure deterministic behaviour
    signal_df = signal_df.sort_values(by=list(signal_df.columns)).reset_index(drop=True)

    truth_col, query_col = identify_signal_columns(signal_df)

    # Create figure with enhanced styling
    plt.figure(figsize=figsize)
    sns.set_style("whitegrid")
    sns.set_palette(color_palette)

    # Create base scatter plot with optional coloring by filter
    if color_source.lower() == "truth" and "FILTER_TRUTH" in signal_df.columns:
        sns.scatterplot(
            data=signal_df,
            x=truth_col,
            y=query_col,
            hue="FILTER_TRUTH",
            alpha=0.5,
            s=50,
        )
    elif color_source.lower() == "query" and "FILTER_QUERY" in signal_df.columns:
        sns.scatterplot(
            data=signal_df,
            x=truth_col,
            y=query_col,
            hue="FILTER_QUERY",
            alpha=0.5,
            s=50,
        )
    elif color_source.lower() == "run":
        sns.scatterplot(
            data=signal_df,
            x=truth_col,
            y=query_col,
            hue="RUN_ID",
            alpha=0.5,
            s=50,
        )
    else:
        plt.scatter(signal_df[truth_col], signal_df[query_col], alpha=0.5, s=50)

    if show_regression:
        # Get unique run IDs, handling NaN values gracefully
        unique_runs = signal_df["RUN_ID"].dropna().astype(str).unique().tolist()
        if len(unique_runs) < 1:
            warnings.warn("No valid RUN_ID found for regression lines.", UserWarning)
            unique_runs = [" "]
            signal_df["RUN_ID"] = " "

        # Set a different color palette for regression lines
        palette = sns.color_palette(color_palette, n_colors=len(unique_runs))
        color_map = dict(zip(unique_runs, palette))

        # Add regression lines for each run if coloring by run
        for idx, run_id in enumerate(unique_runs):
            # Isolate data unique to run
            run_df = signal_df[signal_df["RUN_ID"] == run_id]

            # Add regression line on top of scatter
            sns.regplot(
                x=truth_col,
                y=query_col,
                data=run_df,
                scatter=False,
                line_kws={"alpha": 0.7, "color": color_map[run_id]},
                label=f"Run {run_id}",
            )

            # Calculate correlation and p-value
            corr, p_value = calculate_correlation(run_df)

            # Add correlation statistics to plot
            y_offset = 0.95 - (idx * 0.07)  # Offset to avoid overlap
            plt.text(
                0.05,
                y_offset,
                f"{run_id}: Pearson r = {corr:.3f}\n{run_id}: p-value = {p_value:.2e}",
                transform=plt.gca().transAxes,
                bbox=dict(facecolor="white", alpha=0.8),
            )

    # Customize plot
    plt.xlabel(f"Truth ({truth_col.replace('_TRUTH', '')})")
    plt.ylabel(f"Query ({query_col.replace('_QUERY', '')})")
    plt.title(title)

    # Set axis limits if provided
    if xlim is not None:
        plt.xlim(xlim)
    if ylim is not None:
        plt.ylim(ylim)

    # Save figure with high resolution
    plt.tight_layout()
    plt.savefig(f"{output_filename}.png", dpi=300, bbox_inches="tight")

    # Save PDF with proper vector graphics
    with PdfPages(f"{output_filename}.pdf") as pdf:
        pdf.savefig(bbox_inches="tight", dpi=300)

    plt.close()


def main() -> None:
    """Process signal files and generate correlation plots."""
    parser = argparse.ArgumentParser(
        description="Generate correlation plots from paired signal files."
    )
    parser.add_argument(
        "-t",
        "--truth-signal",
        nargs="+",
        required=True,
        help="Path to the truth signal file(s) or their containing folder.",
    )
    parser.add_argument(
        "-q",
        "--query-signal",
        nargs="+",
        required=True,
        help="Path to the query signal file(s) or their containing folder.",
    )
    parser.add_argument(
        "-o",
        "--output-filename",
        default="signal_correlation",
        help="Base filename (no extension) for scatter plot and table.",
    )
    parser.add_argument(
        "-r",
        "--show-regression",
        action="store_true",
        help="Show regression line and equation.",
    )
    parser.add_argument(
        "-T",
        "--title",
        default="Signal Correlation",
        help="Title for the correlation plot.",
    )
    parser.add_argument(
        "-f",
        "--figsize",
        type=int,
        nargs=2,
        default=[10, 10],
        help="Figure dimensions (width height).",
    )
    parser.add_argument(
        "-x",
        "--xlim",
        type=float,
        nargs=2,
        help="X-axis limits (min max).",
    )
    parser.add_argument(
        "-y",
        "--ylim",
        type=float,
        nargs=2,
        help="Y-axis limits (min max).",
    )
    parser.add_argument(
        "-fs",
        "--color-source",
        choices=["", "truth", "query", "run"],
        default="",
        help="Column to use for coloring ('', 'truth', or 'query').",
    )
    parser.add_argument(
        "--run-pattern",
        default="",
        help=(
            "Pattern used to match run ID from file names for grouping and coloring "
            '(Optional; e.g., "AB\\d{5}").'
        ),
    )
    parser.add_argument(
        "--color-palette",
        default="colorblind",
        help="Color palette to use for plotting (e.g., 'colorblind', 'viridis').",
    )
    args = parser.parse_args()

    # Convert arguments to appropriate types
    truth_signal = [Path(path) for path in args.truth_signal]
    query_signal = [Path(path) for path in args.query_signal]
    output_filename = args.output_filename
    output_table = f"{output_filename}.tsv"
    figsize = tuple(args.figsize)
    xlim = tuple(args.xlim) if args.xlim else None
    ylim = tuple(args.ylim) if args.ylim else None
    run_pattern = args.run_pattern if args.run_pattern else None
    color_palette = args.color_palette

    # Dynamically handle file(s) and folder inputs
    if (
        len(truth_signal) == 1
        and len(query_signal) == 1
        and truth_signal[0].is_dir()
        and query_signal[0].is_dir()
    ):
        # Get all signal files from folders
        truth_signal_files = sorted(truth_signal[0].glob("*.tsv"))
        query_signal_files = sorted(query_signal[0].glob("*.tsv"))

        if not truth_signal_files or not query_signal_files:
            raise ValueError("No signal files found in input folders.")

        # Extract and validate signals
        signal_df = pd.DataFrame()
        for truth_signal_file, query_signal_file in zip(
            truth_signal_files, query_signal_files
        ):
            # Get sample name & run_id from file path
            sample_name = truth_signal_file.with_suffix("").stem.split("_")[0]
            if run_pattern:
                m = re.search(run_pattern, truth_signal_file.name)
                run_id = m.group() if m else None
            else:
                run_id = None

            # Extract signals for this sample
            sample_df = extract_signals(truth_signal_file, query_signal_file)
            if sample_df.empty:
                raise ValueError(
                    f"No matching signals found between {truth_signal_file} and "
                    f"{query_signal_file}."
                )

            # Add sample name & run_id column
            sample_df["SAMPLE"] = sample_name
            sample_df["RUN_ID"] = run_id

            # Append to combined dataframe
            signal_df = pd.concat([signal_df, sample_df], ignore_index=True)
    else:
        if isinstance(truth_signal, list) and isinstance(query_signal, list):
            # Multiple files mode
            signal_df = pd.DataFrame()
            # Sort both lists to ensure consistent pairing
            truth_signal = sorted(truth_signal)
            query_signal = sorted(query_signal)
            for truth_signal_file, query_signal_file in zip(truth_signal, query_signal):
                # Get sample name & run_id from file path
                sample_name = truth_signal_file.with_suffix("").stem.split("_")[0]
                if run_pattern:
                    m = re.search(run_pattern, truth_signal_file.name)
                    run_id = m.group() if m else None
                else:
                    run_id = None

                # Extract signals for this sample
                sample_df = extract_signals(truth_signal_file, query_signal_file)
                if sample_df.empty:
                    raise ValueError(
                        f"No matching signals found between {truth_signal_file} and "
                        f"{query_signal_file}."
                    )

                # Add sample name & run_id column
                sample_df["SAMPLE"] = sample_name
                sample_df["RUN_ID"] = run_id

                # Append to combined dataframe
                signal_df = pd.concat([signal_df, sample_df], ignore_index=True)
        else:
            # Single file mode
            signal_df = extract_signals(truth_signal, query_signal)
            if signal_df.empty:
                raise ValueError(
                    f"No matching signals found between {truth_signal} and "
                    f"{query_signal}."
                )

            # find run pattern
            if run_pattern:
                m = re.search(run_pattern, truth_signal.name)
                run_id = m.group() if m else None
            else:
                run_id = None

            # Add sample name & run_id column
            signal_df["SAMPLE"] = truth_signal.with_suffix("").stem.split("_")[0]
            signal_df["RUN_ID"] = run_id

    # Save signal table
    signal_df.to_csv(output_table, sep="\t", index=False)

    # Generate correlation figure
    plot_signal_correlation(
        signal_df,
        output_filename,
        show_regression=args.show_regression,
        title=args.title,
        figsize=figsize,
        xlim=xlim,
        ylim=ylim,
        color_source=args.color_source,
        color_palette=color_palette,
    )


if __name__ == "__main__":
    main()
