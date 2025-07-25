# TODO: ADD HEADER HERE

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors
import seaborn as sns
import pandas as pd

#target_eval_output_dir = '/projects/gsc_clinical_scratch/cdu/git_repos/clinical_tools/target_evaluation_dragenWGS_all_20250722/target_eval_results'
headers=['CHROM', 'TRACT', 'COVERAGE', 'BASEQ_MEAN', 'BASEQ_Q1', 'MAPQ_MEAN', 'MAPQ_Q1']
#headers=['CHROM', 'TRACT', 'COVERAGE', 'BASEQ_MEAN', 'MAPQ_MEAN']

def main():
    # import glob
    # read input
    #input_files = [Path(file) for file in glob.glob(target_eval_output_dir + '/F*.tract_aggregated.txt') ]

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
        "-p",
        "--prefix",
        default="target_eval",
        help="Prefix for output filenames. Default is 'target_eval'.",
    )
    parser.add_argument(
        "--coverage-threshold",
        help="Coverage threshold to plot.",
    )
    parser.add_argument(
        "--baseq-threshold",
        help="BASEQ threshold to plot.",
    )
    parser.add_argument(
        "--mapq-threshold",
        nargs="+",
        help="MAPQ threshold to plot.",
    )

    args = parser.parse_args()

    input_files = [Path(file_path) for file_path in args.input_files]
    thresholds = {
        "COVERAGE": args.coverage_threshold,
        "BASEQ_MEAN": args.baseq_threshold,
        "MAPQ_MEAN": args.mapq_threshold
    }

    # initialize figure
    fig = plt.figure(figsize=(120, 50))

    # TODO: get pool info from file path
    cmap = plt.get_cmap('viridis')
    dfPools = pd.read_csv(
        '/projects/gsc_clinical_scratch/cdu/git_repos/clinical_tools/target_evaluation_dragenWGS_all_20250718/CCG_Pooled_20250721114953183.csv')
    colors = dict(zip('IX13372,IX13452,IX13471,IX13498,IX13510,IX13523,IX13545,IX13567'.split(','),
                      [cs for cs in sns.color_palette("hls", 8)]))

    for metric in ['COVERAGE','BASEQ_MEAN','MAPQ_MEAN'] :

        for file in input_files:

            # print info
            lib_name=file.name.split(sep='.',maxsplit=1)[0]
            pool = dfPools.loc[dfPools['Library_Name']==lib_name, 'Pool_ID'].values[0]
            print(f"LIBRARY: {lib_name}")
            print(f"FILE {file.name}")
            print(f"POOL {pool}")

            # read data
            df = pd.read_csv(file, sep='\t', header=None)
            df.columns=headers

            # plot graph
            print(colors[pool])
            plt.scatter(data=df, x='TRACT', y=metric, c=matplotlib.colors.rgb2hex(colors[pool]), label=pool)
            plt.axhline(y=thresholds[metric], color='orange', linestyle='--', label='Threshold')

        # plot formatting
        plt.grid(axis='x')
        plt.title(f"{metric} per tract", fontsize=64)
        plt.xticks(rotation=90, ha='right')
        plt.tick_params(axis='x', which='major', labelsize=5)

        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), fontsize=32)
        plt.savefig(f"{args.prefix}_{metric}.png")
        plt.clf()

    print("done")

