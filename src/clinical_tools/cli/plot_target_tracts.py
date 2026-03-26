#!/usr/bin/env python3

"""
Visualize tract/target scores output from target evaluation workflow, grouped by poolID.

Usage:
    plot-target-tracts --input-files <input_files> --pool-ids <pool_ids>
    --metrics-thresholds-and-headings <JSON map of column header to threshold>
    --prefix <prefix>

Example:
    plot-target-tracts --input-files
    A.mpileup.per_base.parsed.labelled.target_aggregated.txt
    B.mpileup.per_base.parsed.labelled.target_aggregated.txt
    C.mpileup.per_base.parsed.labelled.target_aggregated.txt
    --pool-ids IX00001 IX00000 IX12265 --prefix target_eval_visual
    --metrics-thresholds-and-headings
    {"CENTILE100(COV)":25,"CENTILE100(BQ_Q1)":30,"CENTILE100(MQ_Q1)":30}
"""

import argparse
import json
from pathlib import Path

import matplotlib.colors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def main() -> None:
    """Plot target/tract scores by poolID from target evaluation workflow."""
    # Get input parameters
    parser = argparse.ArgumentParser(
        description=("Plot visualizations per-target region.")
    )
    parser.add_argument(
        "-i",
        "--input-files",
        nargs="+",
        help="List of tract aggregated output files to process.",
        required=True,
    )
    parser.add_argument(
        "--pool-ids",
        nargs="+",
        help="List of pool ids corresponding to input files."
        "If not provided, graphs will not be colored",
        default=[],
    )
    parser.add_argument(
        "-p",
        "--prefix",
        default="target_eval",
        help="Prefix for output filenames. Default is 'target_eval'.",
    )
    parser.add_argument(
        "--metrics-thresholds-and-headings",
        type=json.loads,
        help="Dictionary of metric name and threshold.",
        required=True,
    )

    args = parser.parse_args()

    # Convert all filepaths to Path type
    input_files = [Path(file_path) for file_path in args.input_files]

    # Set pools and colors
    pool_ids = (
        args.pool_ids if args.pool_ids != [] else ["No_Pool_Info"] * len(input_files)
    )
    colors = dict(zip(sorted(args.pool_ids), sns.color_palette("hls", len(pool_ids))))
    colors["No_Pool_Info"] = (0.0, 0.0, 1.0)  # default blue points

    # Initialize figure
    plt.figure(figsize=(120, 50))

    for metric, threshold in args.metrics_thresholds_and_headings.items():
        for file, pool in zip(input_files, pool_ids):
            # Read data
            df = pd.read_csv(file, sep="\t", comment=None)
            df.columns = pd.Index([col.lstrip("#") for col in df.columns])
            df[metric] = df[metric].astype(float)

            # Plot graph
            plt.scatter(
                data=df,
                x="TRACT",
                y=metric,
                c=matplotlib.colors.rgb2hex(colors[pool]),
                label=pool,
                alpha=0.8,
            )
            plt.axhline(
                y=threshold,
                color="orange",
                linestyle="--",
                label="Threshold",
            )

        # Format plot
        plt.grid(axis="x")
        plt.title(f"{metric} per tract", fontsize=64)
        plt.xticks(rotation=90, ha="right")
        plt.tick_params(axis="x", which="major", labelsize=5)
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), fontsize=32)

        # Save plot
        plt.savefig(f"{args.prefix}_{metric}.png")
        plt.clf()

    print(f"DONE: All metrics processed and figures saved with prefix {args.prefix}")


if __name__ == "__main__":
    main()
