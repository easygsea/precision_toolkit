#!/usr/bin/env python3

import argparse
import pandas as pd
from clinical_tools.core.metrics.variant import ConcordanceMetrics, VariantCallMetrics
from clinical_tools.render.concordance import (
    export_concordance_to_csv,
    export_concordance_to_markdown,
    export_concordance_to_word,
)


def abbreviation_to_metric(abbreviation):
    """
    Convert a metric abbreviation into its full name.

    Args:
        abbreviation (str): Abbreviation of the metric (e.g., "TP")

    Returns:
        str: Full name of the metric (e.g., "True Positive")

    Note:
        This function assumes a predefined mapping of abbreviations to full names.
    """
    metric_map = {
        'TP': 'True Positive',
        'FN': 'False Negative',
        'FP': 'False Positive'
    }
    return metric_map.get(abbreviation)


def main():
    """
    Main function to manually curate variant concordance summary and export results.

    This script reads a CSV file containing variant concordance summary, updates
    specified metrics based on user input, and then exports the results.

    Args:
        None (arguments are parsed from command line)

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Curate variant concordance from an existing table with count "
                    "information and recompute metrics."
    )
    parser.add_argument(
        "--input", required=True,
        help="Raw concordance summary table (CSV format).")
    parser.add_argument(
        "--curation", nargs='+', action='append',
        required=True,
        help="Curation criteria (type:filter:metric:count).")
    parser.add_argument(
        "--output_prefix", default="curated_concordance",
        help="Prefix for output files (CSV, MD, DOCX).")

    args = parser.parse_args()
    df = pd.read_csv(args.input)

    # Flatten the list of curation criteria
    curations = [item for sublist in args.curation for item in sublist]

    # Update df's metrics based on curation input
    for curation in curations:
        variant_type, filter_type, metric, count = curation.split(':')
        count = int(count)

        metric_full = abbreviation_to_metric(metric)

        # Update the count for matching rows
        mask = (df['Variant Type'] == variant_type) & (
                    df['Variant Filter'] == filter_type)

        # Update metric counts
        df.loc[mask, metric_full] = count

        metrics = VariantCallMetrics(
            VariantType=variant_type,
            VariantCallFilter=filter_type,
            TruthTotal=df.loc[mask, 'True Positive'].sum() + df.loc[
                mask, 'False Negative'].sum(),
            TruthTP=df.loc[mask, 'True Positive'].sum(),
            TruthFN=df.loc[mask, 'False Negative'].sum(),
            QueryTotal=df.loc[mask, 'True Positive'].sum() + df.loc[
                mask, 'False Positive'].sum(),
            QueryTP=df.loc[mask, 'True Positive'].sum(),
            QueryFP=df.loc[mask, 'False Positive'].sum(),
        )

        analysis = ConcordanceMetrics(metrics)
        concordance = analysis.concordance
        ci_lower, ci_upper = analysis.confidence_interval()

        df.loc[mask, "Concordance"] = concordance
        df.loc[mask, "CI Lower"] = ci_lower
        df.loc[mask, "CI Upper"] = ci_upper

    # Since summary_text is not defined, we'll create a simple one
    summary_text = "Curated variant concordance summary."

    # Export using the output prefix
    export_concordance_to_csv(df, f"{args.output_prefix}.csv")
    export_concordance_to_markdown(df, f"{args.output_prefix}.md",
                                   heading="Curated Variant Concordance",
                                   summary=summary_text)
    export_concordance_to_word(df, f"{args.output_prefix}.docx",
                               heading="Curated Variant Concordance",
                               summary=summary_text)


if __name__ == "__main__":
    main()