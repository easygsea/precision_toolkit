"""
Plot backbone-level metrics in DRAGEN's MetricsOutput.tsv file(s).

Usage:
    plot-dragen-metrics --metrics-json-config <config_json>
    --metrics-files <metrics_output_tsv> [<metrics_output_tsv> ...]
    --output-folder <output_folder> [--fastq-list <dragen_fastq_list_csv>]
    [--group-by <column_name_from_fastq_list>] [--sort-by <metric_from_metrics_files>]
    [--truncate-rgsm] [--truncate-rgsm-delim <delimiter_used_to_split_rgsm>]
    [--truncate-rgsm-index <number_of_fields_to_retain>]

Example usage:
    plot-dragen-metrics --metrics-json-config minimal_config.json
    --metrics-files TSO500_MetricsOutput.tsv --output-folder metrics_plots
    --fastq-list fastq_list.csv --group-by 'Sex' --sort-by 'PCT_TARGET_250X (%)'
    --truncate-rgsm --truncate-rgsm-delim '_' --truncate-rgsm-index 1
"""

import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from precision_toolkit.dragen.metrics_parser import DragenMetricsParser
from precision_toolkit.dragen.utils import format_metric


def parse_metrics_output_tsv(
    metrics_file: Path,
    reported_metrics: list[str],
    truncate_rgsm: bool,
    rgsm_delim: str,
    num_rgsm_fields: int,
) -> tuple[pd.DataFrame, dict[str, set[float]]]:
    """Extract specified metrics from MetricsOutput.tsv and return data and limits.

    Args:
        metrics_file: Path to MetricsOutput.tsv.
        reported_metrics: List of metrics to plot, where names should include the units
            (e.g. 'PCT_TARGET_50X (%)').
        truncate_rgsm: Boolean indicating whether to truncate RGSM names.
        rgsm_delim: Delimiter used to split RGSM when truncating.
        num_rgsm_fields: Number of fields to join after splitting RGSM by rgsm_delim.

    Returns:
        A tuple containing:
            - Long-format dataframe of metrics with columns RGSM, Truncated RGSM,
                    Metric (UOM), Value, and Library type.
            - Dictionary mapping metric names to sets of LSL/USL values.
    """
    all_metrics = []
    parsed_guideline_limits: dict[str, set[float]] = defaultdict(set)

    library_type = None
    nan_vals = {"NA", "None", "nan"}
    with open(metrics_file, "r") as metrics_tsv:
        # Tracking per table in case rgsm are not ordered the same between tables
        index_to_rgsm_col = {}
        # Refers to LSL/USL Guidelines only present in TSO500's MetricsOutput.tsv;
        # this, in addition to other guideline limits provided in the JSON config, are
        # used for plot annotation later
        specification_limit_col_indices = []
        for line in metrics_tsv:
            if line.startswith("[") and line.strip().endswith("]"):
                # This applies to TSO500's MetricOutput.tsv where headers preceding
                # each table in the TSV indicate the library type. For custom workflows
                # (e.g. Pan-Heme), it's expected that metrics for only one library type
                # will be present in the input MetricsOutput.tsv.
                library_type = "RNA" if "RNA" in line else "DNA"
            elif line.startswith("Metric (UOM)"):
                col_names = line.strip().split("\t")
                for idx, col_name in enumerate(col_names):
                    if col_name in ("LSL Guideline", "USL Guideline"):
                        specification_limit_col_indices.append(idx)
                    elif col_name != "Metric (UOM)":
                        index_to_rgsm_col[idx] = col_name
            else:
                fields = line.strip().split("\t")
                metric = fields[0]

                if metric not in reported_metrics:
                    continue
                else:
                    parsed_guideline_limits[metric].update(
                        float(fields[idx])
                        for idx in specification_limit_col_indices
                        if fields[idx] not in nan_vals
                    )

                    # Create a separate row for each RGSM's metric value, resulting in a
                    # long-formatted dataframe
                    for idx, rgsm in index_to_rgsm_col.items():
                        row = {
                            "RGSM": rgsm,
                            "Truncated RGSM": (
                                rgsm_delim.join(
                                    rgsm.split(rgsm_delim)[:num_rgsm_fields]
                                )
                                if truncate_rgsm
                                else rgsm
                            ),
                            "Metric (UOM)": metric,
                            "Value": (
                                None if fields[idx] in nan_vals else float(fields[idx])
                            ),
                            "Library type": library_type,
                        }

                        all_metrics.append(row)

    return pd.DataFrame(all_metrics), parsed_guideline_limits


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
    """Return RGSMs sorted alphabetically or by sort_metric in descending order."""
    if sort_metric:
        if sort_metric in df["Metric (UOM)"].values:
            # Grab rows corresponding to sort_metric, then sort values in descending
            # order
            metric_data = df[df["Metric (UOM)"] == sort_metric]
            return metric_data.sort_values("Value", ascending=False)[
                "Truncated RGSM"
            ].tolist()
        else:
            logging.warning(
                f"Sort metric '{sort_metric}' not found in data, sorting alphabetically"
                f"instead."
            )

    # Sort RGSM alphabetically if none specified or sort_metric is not found
    return sorted(df["Truncated RGSM"].unique())


def plot_metrics(
    metrics_df: pd.DataFrame,
    fail_thresholds: dict[str, tuple[float | None, str]],
    guideline_limits: dict[str, set[float | None]],
    group_col: str | None,
    sort_metric: str | None,
    output_folder: Path,
) -> None:
    """Generate and save a strip plot and box plot for each metric.

    Args:
        metrics_df: Long-format dataframe with columns RGSM, Truncated RGSM,
            Metric (UOM), Value, and group_by column.
        fail_thresholds: Dictionary mapping metric names to tuples of threshold values
            and fail direction.
        guideline_limits: Dictionary mapping metric names to guideline limit
            values (LSL, USL).
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
        num_samples = len(plot_data)
        fig_height = max(num_samples * 0.3, 13)  # adjust based on number of samples
        fig, axes = plt.subplots(
            2, 1, figsize=(7, fig_height), gridspec_kw={"height_ratios": [4, 1]}
        )
        fig.suptitle(metric_name)
        plt.subplots_adjust(left=0.35, right=0.76, top=0.95, bottom=0.05)
        sns.set_style("white")
        sns.set_palette("hls", 8)
        # Set default to ensure consistent colors across plots if grouping is disabled
        default_color = sns.color_palette("hls", 8)[0]

        # Plot data
        axes[0] = sns.stripplot(
            data=plot_data,
            x="Value",
            y="Truncated RGSM",
            hue=group_col,
            color=default_color if not group_col else None,
            ax=axes[0],
            order=rgsm_order,
            jitter=False,
            zorder=2,
        )
        axes[0].grid(True, axis="both", ls="-")
        axes[0].set(xlabel=metric_name, ylabel="RGSM")
        axes[1] = sns.boxplot(
            data=plot_data,
            x="Value",
            y=group_col,
            hue=group_col,
            color=default_color if not group_col else None,
            ax=axes[1],
            zorder=2,
        )
        axes[1].grid(True, which="both", axis="both", ls="-")
        axes[1].set(xlabel=metric_name)

        # Plot fail thresholds first so it appears first in legend
        if metric_name in fail_thresholds.keys():
            threshold, direction = fail_thresholds[metric_name]
            if threshold is not None:
                axes[0].axvline(
                    x=threshold,
                    linewidth=2,
                    color="#2E7D32",
                    ls=":",
                    label="Pass\nthreshold",
                    zorder=4,
                )
                axes[1].axvline(
                    x=threshold, linewidth=2, color="#2E7D32", ls=":", zorder=4
                )

                # Shade pass region
                xlim = axes[0].get_xlim()
                pass_boundary = xlim[0] if "greater_than" in direction else xlim[1]
                axes[0].axvspan(
                    threshold,
                    pass_boundary,
                    color="#2E7D32",
                    alpha=0.05,
                    label="Pass",
                    zorder=1,
                )
                axes[1].axvspan(
                    threshold, pass_boundary, color="#2E7D32", alpha=0.05, zorder=1
                )

                # Reset xlim due to addition of axvspan triggering autoscaling of
                # axis limits
                axes[0].set_xlim(xlim)
                axes[1].set_xlim(xlim)

        if metric_name in guideline_limits.keys():
            label_added = False  # track to avoid duplicate labels in legend
            for threshold in guideline_limits[metric_name]:
                if threshold is not None:
                    axes[0].axvline(
                        x=threshold,
                        linewidth=2,
                        color="#4C78A8",
                        ls=":",
                        label="Guideline\nlimit" if not label_added else None,
                        zorder=3,  # plot guideline limits below failure thresholds
                    )
                    axes[1].axvline(
                        x=threshold, linewidth=2, color="#4C78A8", ls=":", zorder=3
                    )
                    label_added = True

        handles, labels = axes[0].get_legend_handles_labels()
        # If pass shading is present, move label to last position in legend
        if "Pass" in labels:
            pass_index = labels.index("Pass")
            handles.append(handles.pop(pass_index))
            labels.append(labels.pop(pass_index))

        # Add and adjust position of legend if there are any handles
        # (i.e. thresholds or groupings)
        if handles:
            axes[0].legend(handles, labels)
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
    """Parse DRAGEN output files and generate QC metric plots."""
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
        help="Column in DRAGEN's fastq list (--fastq-list) to group samples by.",
        default=None,
    )
    parser.add_argument(
        "-s",
        "--sort-by",
        help="Metric name in DRAGEN's MetricsOutput.tsv to sort plots by "
        "(e.g. PCT_TARGET_50X (%)).",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--truncate-rgsm",
        action="store_true",
        help=(
            "By default, the full RGSM is used for plot labels. Enabling this flag "
            "will truncate the RGSM to a shorter sample ID based on "
            "--truncate-rgsm-delimiter and --truncate-rgsm-index."
        ),
    )
    parser.add_argument(
        "-d",
        "--truncate-rgsm-delim",
        help="Delimiter to split RGSM on when truncating. Defaults to '_'.",
        default="_",
    )
    parser.add_argument(
        "-i",
        "--truncate-rgsm-index",
        type=int,
        help=(
            "Fields up to this index (1-based) will be joined after splitting RGSM by "
            "--truncate-rgsm-delimiter."
        ),
        default=1,
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
        sys.exit(1)

    # Create parser just to get metrics to plot and metadata (e.g. UOM, LSL, etc.)
    # for each metric
    dragen_metrics_parser = DragenMetricsParser(metrics_json_config_path, "")

    metrics_to_plot = []
    fail_thresholds = {}
    guideline_limits = {}
    for metric_name in dragen_metrics_parser.reported_metric_names:
        dragen_metric_obj = dragen_metrics_parser.metric_to_metric_obj[metric_name]

        # Get names of metrics to plot
        formatted_metric_name, _ = format_metric(dragen_metric_obj, None)
        metrics_to_plot.append(formatted_metric_name)

        # Set thresholds and limits; default to None if not present
        fail_thresholds[formatted_metric_name] = (
            dragen_metric_obj.fail_threshold,
            dragen_metric_obj.fail_direction,
        )
        metric_attributes = dragen_metric_obj.other_properties
        guideline_limits[formatted_metric_name] = {
            metric_attributes.get("LSL"),
            metric_attributes.get("USL"),
        }

    # Parse each MetricsOutput.tsv and convert into a dataframe with columns RGSM,
    # Truncated RGSM, Metric (UOM), Value, and Library type
    metrics_dfs = []
    for metrics_file in args.metrics_files:
        parsed_metrics_df, parsed_guideline_limits = parse_metrics_output_tsv(
            Path(metrics_file),
            metrics_to_plot,
            args.truncate_rgsm,
            args.truncate_rgsm_delim,
            args.truncate_rgsm_index,
        )
        for metric, limits in parsed_guideline_limits.items():
            guideline_limits[metric] |= limits
        metrics_dfs.append(parsed_metrics_df)
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
            fail_thresholds,
            guideline_limits,
            valid_group_col,
            args.sort_by,
            library_output_folder,
        )

        metrics_with_metadata_df.pivot(
            index=["RGSM", "Truncated RGSM"]
            + ([valid_group_col] if valid_group_col else []),
            columns="Metric (UOM)",
            values="Value",
        ).reset_index().to_csv(
            library_output_folder / "plot_data.csv",
            index=False,
        )


if __name__ == "__main__":
    main()
