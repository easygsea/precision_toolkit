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

from clinical_tools.core.constants import NameMapper
from clinical_tools.core.metrics.variant import PrecisionMetrics, VariantCallMetrics
from clinical_tools.render.diagnostic_metrics import (
    export_diagnostic_metrics_to_csv,
    export_diagnostic_metrics_to_markdown,
    export_diagnostic_metrics_to_word,
)


def validate_curation_format(curation: str) -> bool:
    """Validate manual curation input format.

    Args:
        curation: Manual curation input in format type:filter:metric:count

    Returns:
        True if format is valid

    Raises:
        ValueError: If format is invalid
    """
    try:
        _, _, metric, count = curation.split(":")
        int(count)
        if metric not in {"TP", "FP"}:
            raise ValueError(f"Invalid metric: {metric}. Must be TP or FP.")
        return True
    except ValueError as e:
        raise ValueError(f"Invalid curation format: {e}")


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
        "information and recompute statistics."
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
            validate_curation_format(curation)
    except ValueError as e:
        logging.error(f"Invalid curation format: {e}")
        raise

    # Update counts based on manual input
    for curation in curations:
        variant_type, filter_type, metric, count = curation.split(":")
        count = int(count)

        try:
            metric_full = NameMapper.get_full_name(metric)
        except ValueError as e:
            logging.error(e)
            raise

        mask = (df["Variant Type"] == variant_type) & (
            df["Variant Filter"] == filter_type
        )

        df.loc[mask, metric_full] = count

        metrics = VariantCallMetrics(
            VariantType=variant_type,
            VariantCallFilter=filter_type,
            TruthTotal=df.loc[mask, "True Positive"].sum()
            + df.loc[mask, "False Negative"].sum(),
            TruthTP=df.loc[mask, "True Positive"].sum(),
            TruthFN=df.loc[mask, "False Negative"].sum(),
            QueryTotal=df.loc[mask, "True Positive"].sum()
            + df.loc[mask, "False Positive"].sum(),
            QueryTP=df.loc[mask, "True Positive"].sum(),
            QueryFP=df.loc[mask, "False Positive"].sum(),
        )

        analysis = PrecisionMetrics(metrics)
        precision = analysis.precision
        ci_lower, ci_upper = analysis.confidence_interval()

        df.loc[mask, "Precision"] = precision
        df.loc[mask, "CI Lower"] = ci_lower
        df.loc[mask, "CI Upper"] = ci_upper

    summary_text = "Manually curated precision summary."

    # Export using the output prefix
    export_diagnostic_metrics_to_csv(df, f"{args.output_prefix}.csv")
    export_diagnostic_metrics_to_markdown(
        [df],
        f"{args.output_prefix}.md",
        metric_types=["precision"],
        headings="Manually Curated Precision",
        summaries=summary_text,
    )
    export_diagnostic_metrics_to_word(
        [df],
        f"{args.output_prefix}.docx",
        metric_types=["precision"],
        headings="Manually Curated Precision",
        summaries=summary_text,
    )


if __name__ == "__main__":
    main()
