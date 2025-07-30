# TODO: ADD HEADER HERE

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors
import seaborn as sns
import pandas as pd

def main():

    # Get input parameters
    parser = argparse.ArgumentParser(
        description=("Plot visualizations per-target region.")
    )
    parser.add_argument(
        "-i",
        "--input-files",
        nargs="+",
        help="List of tract aggregated output files to process.",
    )
    parser.add_argument(
        "--pool-ids",
        nargs="+",
        help="List of pool ids corresponding to input files.",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        default="target_eval",
        help="Prefix for output filenames. Default is 'target_eval'.",
    )
    parser.add_argument(
        "--coverage-threshold",
        type=int,
        help="Coverage threshold to plot.",
    )
    parser.add_argument(
        "--baseq-threshold",
        type=int,
        help="BASEQ threshold to plot.",
    )
    parser.add_argument(
        "--mapq-threshold",
        type=int,
        help="MAPQ threshold to plot.",
    )

    args = parser.parse_args()

    input_files = [Path(file_path) for file_path in args.input_files]

    thresholds = {
        "COVERAGE_Q1": args.coverage_threshold,
        "BASEQ_Q1_Q1": args.baseq_threshold,
        "MAPQ_Q1_Q1": args.mapq_threshold
    }

    # set pool colors
    pool_list = set(args.pool_ids)
    colors = dict(zip(pool_list, [cs for cs in sns.color_palette("hls", len(pool_list))]))

    # initialize figure
    fig = plt.figure(figsize=(120, 50))

    for metric in ['COVERAGE_Q1','BASEQ_Q1_Q1','MAPQ_Q1_Q1'] :

        for file,pool in zip(input_files,args.pool_ids):

            # read data
            df = pd.read_csv(file, sep='\t', comment=None)
            df.columns=[col.lstrip('#') for col in df.columns]

            # plot graph
            plt.scatter(data=df, x='TRACT', y=metric, c=matplotlib.colors.rgb2hex(colors[pool]), label=pool, alpha=0.8)
            plt.axhline(y=thresholds[metric], color='orange', linestyle='--', label='Threshold')

        # plot formatting
        plt.grid(axis='x')
        plt.title(f"{metric} Q1 per tract", fontsize=64)
        plt.xticks(rotation=90, ha='right')
        plt.tick_params(axis='x', which='major', labelsize=5)
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), fontsize=32)

        # save plot
        plt.savefig(f"{args.prefix}_{metric}.png")
        plt.clf()

    print("done")
