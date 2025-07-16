#!/usr/bin/env python3
"""Create a BED file with one row per base in the regions of a given a BED file."""

import argparse

import pandas as pd


def main():
    """
    Build a per-base bed from input bed file.

    Args:
        None. Arguments are parsed from command line.

    Returns:
        None. Results are saved to output bed file.
    """
    parser = argparse.ArgumentParser(
        description=("Build a per-base bed from input bed file.")
    )
    parser.add_argument(
        "--input_bed",
        help="BED file input.",
    )
    parser.add_argument(
        "--output_bed",
        help="The output BED file with per-base coordinates.",
    )
    args = parser.parse_args()

    # Read BED file
    bed = pd.read_csv(args.input_bed, sep="\t", header=None)

    # Build per-base bed
    per_base_rows = []
    for _, row in bed.iterrows():
        for position in range(row[1], row[2]):
            per_base_rows.append([row[0], position, position + 1, *row[3:]])

    # Write output
    pd.DataFrame(per_base_rows).to_csv(
        args.output_bed, sep="\t", header=False, index=False
    )


if "__main__" == __name__:
    main()
