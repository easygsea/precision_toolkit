#!/usr/bin/env python3
"""
Manually curate F1 score results.

Usage:
    manual-f1-score-curation --input <input_file>
    --curation <curation_criteria> --output-prefix <output_prefix>
    --decimals <decimals>
Example:
    manual-f1-score-curation --input f1_score.csv
    --curation "SNP:PASS:sensitivity:0.95" "SNP:PASS:precision:0.90"
    --output-prefix manually_curated_f1_score --decimals 1
"""

import argparse
import logging

import pandas as pd

from clinical_tools.core.constants import (
    DEFAULT_CI_LEVEL,
    DEFAULT_CI_METHOD,
    DEFAULT_DECIMALS,
)
from clinical_tools.core.macros.curation.variant import (
    export_curation_results,
    update_metrics,
    validate_curation_format,
)
from clinical_tools.core.metrics.variant import F1ScoreMetrics


def main():
    """
    Manually curate F1 score summary results.

    This script reads a CSV file containing F1 score summary, updates
    specified statistics based on user input, and then exports the results.

    Args:
        None (arguments are parsed from command line)

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Curate F1 score from an existing table with count "
        "information and recompute statistics. Example: "
        "manual-f1-score-curation --input f1_score.csv "
        "--curation 'SNP:PASS:sensitivity:0.95' 'SNP:PASS:precision:0.90' "
        "--output-prefix manually_curated_f1_score --decimals 1"
    )
    parser.add_argument(
        "--input", required=True, help="Input F1 score summary table (CSV format)."
    )
    parser.add_argument(
        "--curation",
        nargs="+",
        action="append",
        required=True,
        help="Manual curation (type:filter:metric:value).",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="manually_curated_f1_score",
        help="Prefix for output files.",
    )
    parser.add_argument(
        "--decimals",
        type=int,
        default=DEFAULT_DECIMALS,
        help=f"Number of decimal places for percentages (default: {DEFAULT_DECIMALS}).",
    )
    args = parser.parse_args()
    df = pd.read_csv(args.input)

    # Flatten the list of curation criteria
    curations = [item for sublist in args.curation for item in sublist]

    # Validate manual curation input before processing
    try:
        for curation in curations:
            validate_curation_format(
                curation,
                valid_metrics=[
                    "sensitivity",
                    "precision",
                    "Sensitivity",
                    "Precision",
                ],
            )
    except ValueError as e:
        logging.error(f"Invalid curation format: {e}")
        raise

    # Update metrics using update_metrics function
    for curation in curations:
        df = update_metrics(
            df,
            curation,
            F1ScoreMetrics,
            DEFAULT_CI_METHOD,
            DEFAULT_CI_LEVEL,
        )

    # Export results
    export_curation_results(df, args.output_prefix, "f1_score", args.decimals)


if __name__ == "__main__":
    main()
