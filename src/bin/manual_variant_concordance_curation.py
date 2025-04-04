#!/usr/bin/env python3
"""
Manually curate variant concordance results.

Usage:
    manual-variant-concordance-curation --input <input_file>
    --curation <curation_criteria> --tp-method <tp_method>
    --output-prefix <output_prefix> --decimals <decimals>
    --ci-method <ci_method> --ci-level <ci_level>

Example:
    manual-variant-concordance-curation --input concordance.csv
    --curation "SNP:PASS:TP:100" "SNP:PASS:FN:50" "SNP:PASS:FP:20"
    --tp-method min --output-prefix manually_curated_concordance --decimals 1
    --ci-method wilson --ci-level 0.95
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
from clinical_tools.core.metrics.variant import (
    ConcordanceMetrics,
    ConcordanceTPMethod,
)
from clinical_tools.core.statistics.proportion import (
    ProportionConfidenceIntervalMethod,
)


def main():
    """
    Manually curate variant concordance summary results.

    This script reads a CSV file containing variant concordance summary, updates
    specified statistics based on user input, and then exports the results.

    Args:
        None (arguments are parsed from command line)

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Curate variant concordance from an existing table with count "
        "information and recompute statistics. Example: "
        "manual-variant-concordance-curation --input concordance.csv "
        "--curation 'SNP:PASS:TP:100' 'SNP:PASS:FN:50' 'SNP:PASS:FP:20' "
        "--tp-method min --output-prefix manually_curated_concordance --decimals 1 "
        "--ci-method wilson --ci-level 0.95"
    )
    parser.add_argument(
        "--input", required=True, help="Input concordance summary table (CSV format)."
    )
    parser.add_argument(
        "--curation",
        nargs="+",
        action="append",
        required=True,
        help="Manual curation (type:filter:metric:count).",
    )
    parser.add_argument(
        "--tp-method",
        choices=[method.value for method in ConcordanceTPMethod],
        default=ConcordanceTPMethod.MinTP.value,
        help=f"TP method in concordance (default: {ConcordanceTPMethod.MinTP.value}).",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="manually_curated_concordance",
        help="Prefix for output files.",
    )
    parser.add_argument(
        "--decimals",
        type=int,
        default=DEFAULT_DECIMALS,
        help=f"Number of decimal places for percentages (default: {DEFAULT_DECIMALS}).",
    )
    parser.add_argument(
        "--ci-method",
        type=str,
        choices=[method.value for method in ProportionConfidenceIntervalMethod],
        default=DEFAULT_CI_METHOD,
        help="Statistical method for confidence interval calculation "
        f"(default: {DEFAULT_CI_METHOD}).",
    )
    parser.add_argument(
        "--ci-level",
        type=float,
        default=DEFAULT_CI_LEVEL,
        help="Confidence level for confidence intervals (default: "
        f"{DEFAULT_CI_LEVEL}).",
    )

    args = parser.parse_args()
    df = pd.read_csv(args.input)

    # Flatten the list of curation criteria
    curations = [item for sublist in args.curation for item in sublist]

    # Validate manual curation input before processing
    try:
        for curation in curations:
            validate_curation_format(curation, valid_metrics=["TP", "FN", "FP"])
    except ValueError as e:
        logging.error(f"Invalid curation format: {e}")
        raise

    # Update counts and recalculate metrics
    for curation in curations:
        df = update_metrics(
            df,
            curation,
            ConcordanceMetrics,
            args.tp_method,
            args.ci_method,
            args.ci_level,
        )

    # Export results
    export_curation_results(df, args.output_prefix, "concordance", args.decimals)


if __name__ == "__main__":
    main()
