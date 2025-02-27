#!/usr/bin/env python3
"""
Manually curate variant concordance results.

Usage:
    curate-variant-concordance --input <input_file> --curation <curation_criteria>
    --output_prefix <output_prefix>

Example:
    curate-variant-concordance --input concordance.csv --curation "SNP:PASS:TP:100"
    "SNP:PASS:FN:50" "SNP:PASS:FP:20" --output_prefix manually_curated_concordance
"""

import argparse
import logging

import pandas as pd

from clinical_tools.core.constants import NameMapper
from clinical_tools.core.metrics.variant import ConcordanceMetrics, VariantCallMetrics
from clinical_tools.render.variant_concordance import (
    export_concordance_to_csv,
    export_concordance_to_markdown,
    export_concordance_to_word,
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
        if metric not in {"TP", "FN", "FP"}:
            raise ValueError(f"Invalid metric: {metric}")
        return True
    except ValueError as e:
        raise ValueError(f"Invalid curation format: {e}")


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
        "information and recompute statistics."
    )
    parser.add_argument(
        "--input", required=True, help="Raw concordance summary table (CSV format)."
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
        default="manually_curated_concordance",
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

        analysis = ConcordanceMetrics(metrics)
        concordance = analysis.concordance
        ci_lower, ci_upper = analysis.confidence_interval()

        df.loc[mask, "Concordance"] = concordance
        df.loc[mask, "CI Lower"] = ci_lower
        df.loc[mask, "CI Upper"] = ci_upper

    summary_text = "Manually curated variant concordance summary."

    # Export using the output prefix
    export_concordance_to_csv(df, f"{args.output_prefix}.csv")
    export_concordance_to_markdown(
        df,
        f"{args.output_prefix}.md",
        headings="Manually Curated Variant Concordance",
        summaries=summary_text,
    )
    export_concordance_to_word(
        df,
        f"{args.output_prefix}.docx",
        headings="Manually Curated Variant Concordance",
        summaries=summary_text,
    )


if __name__ == "__main__":
    main()
