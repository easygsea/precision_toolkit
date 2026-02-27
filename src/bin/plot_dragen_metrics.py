"""
Plot backbone-level metrics in DRAGEN's MetricsOutput.tsv file(s).

Usage:
    plot-dragen-metrics --metrics-json-config <json_config>
    --metrics-files <metrics_output_tsv> [<metrics_output_tsv> ...]
    --output-folder <output_folder> [--fastq-list <dragen_fastq_list>]
    [--group-by <fastq_list_column_to_group_by>] [--sort-by <metric_to_sort_by>]

Example usage:
    plot-dragen-metrics --metrics-json-config minimal_config.json
    --metrics-files TSO500_MetricsOutput.tsv --output-folder metrics_plots
    --fastq-list /path/to/fastq_list.csv --group-by Pool --sort-by PCT_TARGET_50X (%)
"""

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from clinical_tools.dragen.metrics_parser import DragenMetricsParser
from clinical_tools.dragen.utils import format_metric


def parse_metrics_output_tsv(
    metrics_file: Path, reported_metrics: list[str]
) -> pd.DataFrame:
    """
    Parse specified metrics from MetricsOutput.tsv and returns dataframes.

    Args:
        metrics_file: Path to MetricsOutput.tsv.
        reported_metrics: List of metrics to plot, where names should include the units
            (e.g. PCT_TARGET_50X (%)).

    Returns:
        Long-format dataframe of metrics with columns RGSM, Metrics (UOM), Value, and
        Library type.
    """
    all_metrics = []

    library_type = None
    with open(metrics_file, "r") as metrics_tsv:
        # Tracking per table in case rgsm are not ordered the same between tables
        index_to_rgsm_col = {}
        for line in metrics_tsv:
            if line.startswith("[") and line.strip().endswith("]"):
                # This applies to TSO500's MetricOutput.tsv where headers preceding
                # each table in the TSV indicate the library type. For custom workflows
                # (e.g. Pan-Heme), it's expected that metrics for only one library type
                # will be present in the input MetricsOutput.tsv.
                library_type = "RNA" if "RNA" in line else "DNA"
            elif line.startswith("Metric (UOM)"):
                col_names = line.strip().split("\t")
                index_to_rgsm_col = {
                    idx: col_name
                    for idx, col_name in enumerate(col_names)
                    if col_name
                    not in ("USL Guideline", "LSL Guideline", "Metric (UOM)")
                }
            else:
                fields = line.strip().split("\t")
                metric = fields[0]

                if metric not in reported_metrics:
                    continue
                else:
                    # Create a separate row for each RGSM's value then append to
                    # appropriate list (dna/rna_library_metrics)
                    for idx, rgsm in index_to_rgsm_col.items():
                        row = {
                            "RGSM": rgsm,
                            "Metric (UOM)": metric,
                            "Value": (
                                float(fields[idx]) if fields[idx] != "None" else None
                            ),
                            "Library type": library_type,
                        }

                        all_metrics.append(row)

    return pd.DataFrame(all_metrics)


def get_rgsm_groupings(
    fastq_list_file: Path, group_by: str
) -> tuple[pd.DataFrame, str | None]:
    """Validate group_by column name, then return a dataframe mapping RGSM to column."""
    fastq_list_df = pd.read_csv(fastq_list_file)

    # Check if group_by column is present
    if group_by not in fastq_list_df.columns:
        logging.warning(
            f"'{group_by}' column not found in FASTQ list, grouping won't be applied."
        )
        valid_group_col = None
    else:
        valid_group_col = group_by

    # Return dataframe mapping RGSM to group_by column
    fastq_list_df_unique = fastq_list_df.drop_duplicates(subset=["RGSM"], keep="first")
    cols = ["RGSM"] + ([valid_group_col] if valid_group_col else [])
    return fastq_list_df_unique[cols], valid_group_col


def determine_rgsm_order(df: pd.DataFrame, sort_metric: str | None) -> list[str]:
    """Return RGSMs sorted by RGSM or by sort_metric, if specified."""
    if sort_metric:
        if sort_metric in df["Metric (UOM)"].values:
            # Grab rows corresponding to sort_metric, then sort values in descending
            # order
            metric_data = df[df["Metric (UOM)"] == sort_metric]
            return metric_data.sort_values("Value", ascending=False)["RGSM"].tolist()
        else:
            logging.warning(
                f"Sort metric '{sort_metric}' not found in data, sorting alphabetically"
                f"instead."
            )

    # Sort RGSM alphabetically if none specified or sort_metric is not found
    return sorted(df["RGSM"].unique())


def plot_metrics(
    metrics_df: pd.DataFrame,
    thresholds: dict[str, list[float | None]],
    proposed_thresholds: dict[str, list[float | None]],
    group_col: str | None,
    sort_metric: str | None,
    output_folder: Path,
) -> None:
    """
    Generate and save a strip plot and box plot for each metric.

    Args:
        metrics_df: Long-format dataframe with columns RGSM, Metric (UOM), Value, and
            group_by column.
        thresholds: Dictionary mapping metric names to threshold values (LSL and USL).
        proposed_thresholds: Dictionary mapping metric names to proposed threshold
            values (PROPOSED_LSL, PROPOSED_USL).
        group_col: Column name to group samples by in plots, or None.
        sort_metric: Metric to sort plots by, in descending order, or None to sort by
            RGSM alphabetically.
        output_folder: Directory to save plots to.
    """
    # Ensure output folder is created
    output_folder.mkdir(parents=True, exist_ok=True)

    rgsm_order = determine_rgsm_order(metrics_df, sort_metric)
    for metric_name in metrics_df["Metric (UOM)"].unique():
        plot_data = metrics_df[metrics_df["Metric (UOM)"] == metric_name]

        # If all values are NA, skip
        if plot_data["Value"].isna().all():
            logging.warning(
                f"Skipping plot for {metric_name} values for all samples are NA."
            )
            continue

        # Set up plot area
        fig, axes = plt.subplots(
            2, 1, figsize=(7, 13), gridspec_kw={"height_ratios": [4, 1]}
        )
        fig.suptitle(metric_name)
        plt.subplots_adjust(left=0.35, right=0.76, top=0.95, bottom=0.05)
        sns.set_style("white")
        sns.set_palette("hls", 8)

        # Plot data
        axes[0] = sns.stripplot(
            data=plot_data,
            x="Value",
            y="RGSM",
            hue=group_col,
            ax=axes[0],
            order=rgsm_order,
        )
        axes[0].grid(True, axis="both", ls="-")
        axes[0].set(xlabel=metric_name)
        axes[1] = sns.boxplot(
            data=plot_data, x="Value", y=group_col, hue=group_col, ax=axes[1]
        )
        axes[1].grid(True, which="both", axis="both", ls="-")
        axes[1].set(xlabel=metric_name)

        # Add thresholds, if available
        if metric_name in thresholds.keys():
            for threshold in thresholds[metric_name]:
                if threshold is not None:
                    axes[0].axvline(
                        x=threshold,
                        linewidth=2,
                        color="orange",
                        ls=":",
                        label="Threshold",
                    )
                    axes[1].axvline(x=threshold, linewidth=2, color="orange", ls=":")

        if metric_name in proposed_thresholds.keys():
            for threshold in proposed_thresholds[metric_name]:
                if threshold is not None:
                    axes[0].axvline(
                        x=threshold, linewidth=2, color="blue", ls=":", label="Proposed"
                    )
                    axes[1].axvline(x=threshold, linewidth=2, color="blue", ls=":")

        # Add and adjust position of legend if there are any handles
        # (i.e. thresholds or groupings)
        handles, _ = axes[0].get_legend_handles_labels()
        if handles:
            axes[0].legend()
            sns.move_legend(
                axes[0],
                "center right",
                bbox_to_anchor=(1.54, 0.5),
                ncol=1,
                title=group_col,
            )

        # Save plots and clean space
        plt.savefig(
            f"{output_folder}/{metric_name}.png", bbox_inches="tight", pad_inches=0.3
        )
        plt.close()


def main() -> None:
    """
    Parse DRAGEN output files and plot QC metrics.

    Returns:
        None, saves plots to PNG files.
    """
    parser = argparse.ArgumentParser(
        "Parse DRAGEN's MetricsOutput.tsv and generate summary plots per metric."
    )
    parser.add_argument(
        "-j",
        "--metrics-json-config",
        help="Path to JSON with source files and formatting attributes for metrics.",
        required=True,
    )
    parser.add_argument(
        "-m",
        "--metrics-files",
        nargs="+",
        help="Path(s) DRAGEN's MetricsOutput.tsv file(s).",
        required=True,
    )
    parser.add_argument(
        "-f",
        "--fastq-list",
        help="Path to DRAGEN's fastq list, required if grouping is desired.",
    )
    parser.add_argument(
        "-g",
        "--group-by",
        help="Column in DRAGEN's fastq list to group samples by.",
        default=None,
    )
    parser.add_argument(
        "-s",
        "--sort-by",
        help="Metric name to sort plots by (e.g. PCT_TARGET_50X (%)).",
        default=None,
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        help="Name of folder to output QC plots.",
        required=True,
    )

    # Parse args
    args = parser.parse_args()
    metrics_json_config_path = Path(args.metrics_json_config)
    group_by = args.group_by
    fastq_list_file_path = Path(args.fastq_list) if args.fastq_list else None
    output_folder = Path(args.output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)

    # Validate args
    if group_by and not fastq_list_file_path:
        logging.error("--group-by requires --fastq-list to be provided.")
        exit()

    # Create parser just to get metrics to plot and metadata (e.g. UOM, LSL, etc.)
    # for each metric
    dragen_metrics_parser = DragenMetricsParser(metrics_json_config_path, Path(), "")

    metrics_to_plot = []
    thresholds = {}
    proposed_thresholds = {}
    for metric_name in dragen_metrics_parser.reported_metric_names:
        dragen_metric_obj = dragen_metrics_parser.metric_to_metric_obj[metric_name]

        # Get names of metrics to plot
        formatted_metric_name, _ = format_metric(dragen_metric_obj, None)
        metrics_to_plot.append(formatted_metric_name)

        # Set thresholds and proposed thresholds; default to None if not present
        metric_attributes = dragen_metric_obj.other_properties
        thresholds[formatted_metric_name] = [
            metric_attributes.get("LSL"),
            metric_attributes.get("USL"),
        ]
        proposed_thresholds[formatted_metric_name] = [
            metric_attributes.get("PROPOSED_LSL"),
            metric_attributes.get("PROPOSED_USL"),
        ]

    # Parse each MetricsOutput.tsv and convert into a dataframe with columns RGSM,
    # Metric (UOM), Value, and Library type
    metrics_dfs = []
    for metrics_file in args.metrics_files:
        metrics_dfs.append(
            parse_metrics_output_tsv(Path(metrics_file), metrics_to_plot)
        )
    metrics_df = pd.concat(metrics_dfs, ignore_index=True)

    # If grouping is desired, parse FASTQ list to reliably get groupings for each RGSM
    rgsm_to_metadata_df = pd.DataFrame(columns=["RGSM"])
    valid_group_col = None
    if group_by and fastq_list_file_path:
        rgsm_to_metadata_df, valid_group_col = get_rgsm_groupings(
            fastq_list_file_path, group_by
        )

    # Generate plots and write plot data to file
    for library_type, library_metrics_df in metrics_df.groupby(
        "Library type", dropna=False
    ):
        metrics_with_metadata_df = (
            library_metrics_df.drop(columns="Library type")
            .merge(rgsm_to_metadata_df, on="RGSM", how="left")
            .fillna({valid_group_col: "Unknown"} if valid_group_col else {})
        )

        # Set output folder depending on library_type
        library_output_folder = (
            output_folder
            if pd.isna(library_type)
            else output_folder / str(library_type)
        )

        plot_metrics(
            metrics_with_metadata_df,
            thresholds,
            proposed_thresholds,
            valid_group_col,
            args.sort_by,
            library_output_folder,
        )

        metrics_with_metadata_df.pivot(
            index=["RGSM"] + ([valid_group_col] if valid_group_col else []),
            columns="Metric (UOM)",
            values="Value",
        )


if __name__ == "__main__":
    main()
