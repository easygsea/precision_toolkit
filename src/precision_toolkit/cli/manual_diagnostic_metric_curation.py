#!/usr/bin/env python3
"""
Manually curate a diagnostic metric.

Usage:
    manual-diagnostic-metric-curation metric --input <input_file>
    --curation <curation_criteria> --tp-method <tp_method>
    --output-prefix <output_prefix> --decimals <decimals>
    --ci-method <ci_method> --ci-level <ci_level>

Example:
    manual-diagnostic-metric-curation concordance --input metric.csv
    --curation "SNP:PASS:TP:100" "SNP:PASS:FN:50" "SNP:PASS:FP:20"
    --tp-method min --output-prefix manually_curated_concordance --decimals 1
    --ci-method wilson --ci-level 0.95
"""

import argparse
import logging

import pandas as pd

from precision_toolkit.core.constants import (
    DEFAULT_CI_LEVEL,
    DEFAULT_CI_METHOD,
    DEFAULT_DECIMALS,
    DiagnosticMetricType,
)
from precision_toolkit.core.macros.curation.variant import (
    export_curation_results,
    update_metrics,
    validate_curation_format,
)
from precision_toolkit.core.metrics.variant import (
    ConcordanceTPMethod,
)
from precision_toolkit.core.statistics.proportion import (
    ProportionConfidenceIntervalMethod,
)


def main() -> None:
    """Manually curate a diagnostic metric from a CSV and export updated results."""
    parser = argparse.ArgumentParser(
        description="Curate diagnostic metrics from an existing table with count "
        "information and recompute statistics. Example: "
        "manual-diagnostic-metric-curation concordance --input metric.csv "
        "--curation 'SNP:PASS:TP:100' 'SNP:PASS:FN:50' 'SNP:PASS:FP:20' "
        "--tp-method min --output-prefix manually_curated_concordance --decimals 1 "
        "--ci-method wilson --ci-level 0.95"
    )
    parser.add_argument(
        "metric",
        choices=DiagnosticMetricType,
        type=DiagnosticMetricType,
        help="Diagnostic metric to curate.",
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

    # Set conditional requirements after parsing
    if args.metric == DiagnosticMetricType.CONCORDANCE:
        parser.set_defaults(tp_method=args.tp_method)
    elif args.metric == DiagnosticMetricType.F1_SCORE:
        parser.set_defaults(ci_method=None, ci_level=None)

    # Set default output prefix if not provided
    if not args.output_prefix:
        args.output_prefix = f"manually_curated_{args.metric}"

    df = pd.read_csv(args.input)

    # Flatten the list of curation criteria
    curations = [item for sublist in args.curation for item in sublist]

    # Validate manual curation input before processing
    valid_metrics = {
        "concordance": ["TP", "FN", "FP"],
        "sensitivity": ["TP", "FN"],
        "precision": ["TP", "FP"],
        "f1_score": ["sensitivity", "precision"],
    }[args.metric]
    try:
        for curation in curations:
            validate_curation_format(curation, valid_metrics=valid_metrics)
    except ValueError as e:
        logging.error(f"Invalid curation format: {e}")
        raise

    # Update counts and recalculate metrics
    for curation in curations:
        df = update_metrics(
            df,
            curation,
            args.metric,
            args.tp_method,
            args.ci_method,
            args.ci_level,
        )

    # Export results
    export_curation_results(df, args.output_prefix, args.metric, args.decimals)


if __name__ == "__main__":
    main()
