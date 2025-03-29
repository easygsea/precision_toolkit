#!/usr/bin/env python3
"""
Manually curate precision results.

Usage:
    manual-precision-curation --input <input_file>
    --curation <curation_criteria> --output_prefix <output_prefix>

Example:
    manual-precision-curation --input precision.csv
    --curation "SNP:PASS:TP:100" "SNP:PASS:FP:50"
    --output_prefix manually_curated_precision
"""

import argparse
import logging

import pandas as pd

from clinical_tools.core.macros.curation.variant import (
    export_curation_results,
    update_metrics,
    validate_curation_format,
)
from clinical_tools.core.metrics.variant import PrecisionMetrics


def main():
    """
    Manually curate precision summary results.

    This script reads a CSV file containing precision summary, updates
    specified statistics based on user input, and then exports the results.

    Args:
        None (arguments are parsed from command line)

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Curate precision from an existing table with count "
        "information and recompute statistics. Example: "
        "manual-precision-curation --input precision.csv "
        "--curation 'SNP:PASS:TP:100' 'SNP:PASS:FP:50' "
        "--output_prefix manually_curated_precision"
    )
    parser.add_argument(
        "--input", required=True, help="Input precision summary table (CSV format)."
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
        default="manually_curated_precision",
        help="Prefix for output files.",
    )

    args = parser.parse_args()
    df = pd.read_csv(args.input)

    # Flatten the list of curation criteria
    curations = [item for sublist in args.curation for item in sublist]

    # Validate manual curation input before processing
    try:
        for curation in curations:
            validate_curation_format(curation, valid_metrics=["TP", "FP"])
    except ValueError as e:
        logging.error(f"Invalid curation format: {e}")
        raise

    # Update counts and recalculate metrics
    for curation in curations:
        df = update_metrics(df, curation, PrecisionMetrics)

    # Export results
    export_curation_results(df, args.output_prefix, "precision")


if __name__ == "__main__":
    main()
