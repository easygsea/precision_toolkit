#!/usr/bin/env python3

"""
Visualize gene fail scores output from target evaluation workflow.

Usage:
    plot-gene-boxplots --input-file <input_file>
    [--threshold <fail_analysis_threshold>]  [--separate-plots]

Example:
    plot-gene-boxplots --input-file cohort_base_analysis.tsv
    --threshold 25
    --separate-plots
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

CUSTOM_COLORS = {
    "Coverage (%)": "#648FFF",
    "Base Quality (%)": "#DC267F",
    "Mapping Quality (%)": "#FFB000",
}


def threshold_type(value: str) -> float:
    """Convert input to float and validate that it falls between 1 and 100."""
    try:
        f = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid number")
    if not (1 <= f <= 100):
        raise argparse.ArgumentTypeError(
            f"Threshold must be between 1 and 100, got {f}"
        )
    return f


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean columns and melt data for later plotting."""
    df.columns = df.columns.str.lstrip("#")
    df["GENE"] = df["TRACT"].str.split("_").str[0]

    cols_to_plot = {
        "PCT_LIB_FAIL(COV)": "Coverage (%)",
        "PCT_LIB_FAIL(BQ)": "Base Quality (%)",
        "PCT_LIB_FAIL(MQ)": "Mapping Quality (%)",
    }

    df_melted = df.melt(
        id_vars=["GENE"],
        value_vars=list(cols_to_plot.keys()),
        var_name="Metric",
        value_name="Value",
    )
    df_melted["Metric"] = df_melted["Metric"].map(cols_to_plot)

    return df_melted


def get_gene_groups(df: pd.DataFrame) -> list[np.ndarray]:
    """Determine how many subplots are needed based on gene count."""
    all_genes_arr = np.array(sorted(df["GENE"].unique()))

    if len(all_genes_arr) >= 3:
        return np.array_split(all_genes_arr, 3)
    return [all_genes_arr]


def create_plot(
    df_melted: pd.DataFrame, gene_groups: list, threshold: float, separate_plots: bool
) -> list[tuple[Figure, str]]:
    """Plot per-base quality metrics."""
    sns.set_style("whitegrid")

    figures = []

    metrics = df_melted["Metric"].unique()

    if separate_plots:
        metrics_to_plot = [[m] for m in metrics]
    else:
        metrics_to_plot = [list(metrics)]

    for metric_group in metrics_to_plot:
        metric_name = "combined" if not separate_plots else metric_group[0]

        fig, axes = plt.subplots(
            nrows=len(gene_groups), ncols=1, figsize=(20, 8 * len(gene_groups))
        )

        if len(gene_groups) == 1:
            axes = [axes]

        for i, group in enumerate(gene_groups):
            ax = axes[i]
            subset = df_melted[
                (df_melted["GENE"].isin(group))
                & (df_melted["Metric"].isin(metric_group))
            ]

            sns.boxplot(
                data=subset,
                x="GENE",
                y=100 - subset["Value"],
                hue="Metric",
                palette=CUSTOM_COLORS,
                ax=ax,
            )

            sns.stripplot(
                data=subset,
                x="GENE",
                y=100 - subset["Value"],
                hue="Metric",
                dodge=True,
                alpha=0.4,
                size=1.5,
                palette=CUSTOM_COLORS,
                legend=False,
                ax=ax,
            )

            ax.set_ylabel("Percentage of all libraries passing per base", fontsize=12)
            ax.set_xlabel("Gene", fontsize=12)
            ax.tick_params(axis="x", rotation=90, labelsize=10)

            ax.set_ylim(-5, 105)

            ax.axhline(
                y=(100 - threshold),
                color="red",
                linestyle="--",
                alpha=0.7,
                label=f"Minimum Percentage of Passing Libraries ({100 - threshold}%)",
            )
            if i == 0:
                ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", title="Metric")
            else:
                if ax.get_legend():
                    ax.get_legend().remove()

        plt.suptitle(
            f"Cohort pass rate for each base in target space "
            f"grouped by gene ({metric_name})",
            fontsize=32,
            y=0.98,
        )

        plt.subplots_adjust(left=0.05, right=0.85, top=0.94, bottom=0.05, hspace=0.6)
        figures.append((fig, metric_name))

    return figures


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=("Plot gene-level failure distributions.")
    )
    parser.add_argument(
        "-i",
        "--input-file",
        required=True,
        help="Path to cohort_base_analysis.tsv file",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=threshold_type,
        default=25.0,
        help=(
            "Maximum percentage of libraries allowed to fail at a given base "
            "(default: 25, not inclusive)"
        ),
    )
    parser.add_argument(
        "-s",
        "--separate-plots",
        action="store_true",
        help="Flag to separate metric plots into distinct figures (default: false)",
    )
    return parser.parse_args()


def main() -> None:
    """Process txt file and threshold then call functions to generate box plot."""
    args = parse_args()
    original_df = pd.read_csv(args.input_file, sep="\t")

    processed_df = prepare_dataframe(original_df)
    groups = get_gene_groups(processed_df)

    figs = create_plot(processed_df, groups, args.threshold, args.separate_plots)

    for fig, metric_name in figs:
        if not args.separate_plots:
            output_name = f"failure_threshold_{args.threshold}_boxplot.png"
        else:
            metric_translated = (
                metric_name.replace(" ", "_").replace("%", "").replace("()", "")
            )
            output_name = (
                f"failure_threshold_{args.threshold}_"
                f"boxplot_{metric_translated[:-1].lower()}.png"
            )

        fig.savefig(output_name, dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()
