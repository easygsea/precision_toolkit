#!/usr/bin/env python3
"""
Manually curate sensitivity results.

Usage:
    manual-sensitivity-curation --input <input_file>
    --curation <curation_criteria> --output_prefix <output_prefix>
    --decimals <decimals>
Example:
    manual-sensitivity-curation --input sensitivity.csv
    --curation "SNP:PASS:TP:100" "SNP:PASS:FN:50"
    --output_prefix manually_curated_sensitivity --decimals 1
"""

import argparse
import logging

import pandas as pd

from clinical_tools.core.constants import DEFAULT_DECIMALS
from clinical_tools.core.macros.curation.variant import (
    export_curation_results,
    update_metrics,
    validate_curation_format,
)
from clinical_tools.core.metrics.variant import SensitivityMetrics


def main():
    """
    Manually curate sensitivity summary results.

    This script reads a CSV file containing sensitivity summary, updates
    specified statistics based on user input, and then exports the results.

    Args:
        None (arguments are parsed from command line)

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Curate sensitivity from an existing table with count "
        "information and recompute statistics. Example: "
        "manual-sensitivity-curation --input sensitivity.csv "
        "--curation SNP:PASS:TP:100 'SNP:PASS:FN:50' "
        "--output_prefix manually_curated_sensitivity --decimals 1"
    )
    parser.add_argument(
        "--input", required=True, help="Input sensitivity summary table (CSV format)."
    )
    parser.add_argument(
        "--curation",
        nargs="+",
        action="append",
        required=True,
        help="Manual curation (type:filter:metric:count).",
    )
    parser.add_argument(
        "--output_prefix",
        default="manually_curated_sensitivity",
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
            validate_curation_format(curation, valid_metrics=["TP", "FN"])
    except ValueError as e:
        logging.error(f"Invalid curation format: {e}")
        raise

    # Update counts and recalculate metrics
    for curation in curations:
        df = update_metrics(df, curation, SensitivityMetrics)

    # Export results
    export_curation_results(df, args.output_prefix, "sensitivity", args.decimals)


if __name__ == "__main__":
    main()
