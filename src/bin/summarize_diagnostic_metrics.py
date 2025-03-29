#!/usr/bin/env python3
"""
Summarize and compute diagnostic metrics from VCF comparisons.

Usage:
    summarize-diagnostic-metrics --engine <engine> --raw-files <raw_files>
    --curated-files <curated_files> --prefix <prefix> --metrics <metrics>
    --tp-method <concordance true positive method: truth, query, or min>

Example:
    summarize-diagnostic-metrics --engine happy --raw-files A.raw.summary.csv
    B.raw.summary.csv --curated-files A.curated.summary.csv B.curated.summary.csv
    --prefix diagnostic_metrics --metrics concordance sensitivity precision
    --tp-method min
"""

import argparse

import pandas as pd

from clinical_tools.analysis.diagnostic_metrics import process_diagnostic_metrics
from clinical_tools.core.constants import (
    DiagnosticMetricType,
    VariantConcordanceEngine,
)
from clinical_tools.core.metrics.variant import ConcordanceTPMethod
from clinical_tools.render.diagnostic_metrics import (
    export_diagnostic_metrics_to_csv,
    export_diagnostic_metrics_to_markdown,
    export_diagnostic_metrics_to_word,
    generate_diagnostic_metrics_table,
)


def main():
    """
    Summarize and compute diagnostic metrics from VCF comparisons.

    Args:
        None. Arguments are parsed from command line.

    Returns:
        None. Results are saved to CSV, Markdown, and Word files.
    """
    parser = argparse.ArgumentParser(
        description=("Summarize and compute diagnostic metrics from VCF comparisons.")
    )
    parser.add_argument(
        "-e",
        "--engine",
        choices=[engine.value for engine in VariantConcordanceEngine],
        required=True,
        help="Engine output format: 'happy' or 'wittyer'.",
    )
    parser.add_argument(
        "-f",
        "--raw-files",
        nargs="+",
        help="List of raw engine output files to process.",
    )
    parser.add_argument(
        "-c",
        "--curated-files",
        nargs="+",
        help="List of curated engine output files to process.",
    )
    parser.add_argument(
        "--tp-method",
        choices=[method.value for method in ConcordanceTPMethod],
        default=ConcordanceTPMethod.MinTP.value,
        help="TP method in concordance: 'truth', 'query', or 'min' (default).",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        default="diagnostic_metrics",
        help="Prefix for output filenames. Default is 'diagnostic_metrics'.",
    )
    parser.add_argument(
        "-m",
        "--metrics",
        nargs="+",
        choices=["concordance", "sensitivity", "precision"],
        default=["concordance", "sensitivity", "precision"],
        help="Metrics to compute. Multiple metrics separated by spaces. "
        "Options: concordance, sensitivity, precision. Default is all metrics.",
    )

    args = parser.parse_args()

    # Validate that at least one of raw-files or curated-files is provided
    if not args.raw_files and not args.curated_files:
        parser.error("At least one of --raw-files or --curated-files must be provided")

    # Determine output prefix suffix based on provided files
    if args.raw_files and args.curated_files:
        suffix = "combined"
    elif args.raw_files:
        suffix = "raw"
    else:
        suffix = "curated"
    output_prefix = f"{args.prefix}_{args.engine}_{suffix}"

    # Initialize tables, headings and summaries
    raw_tables: list[pd.DataFrame] = []
    curated_tables: list[pd.DataFrame] = []
    raw_headings: list[str] = []
    curated_headings: list[str] = []
    raw_summaries: list[str] = []
    curated_summaries: list[str] = []
    initial_metric_types: list[DiagnosticMetricType] = []

    # Process raw VCF comparisons
    if args.raw_files:
        raw_results = process_diagnostic_metrics(
            file_paths=args.raw_files,
            data_type=args.engine,
            tp_method=args.tp_method,
            metrics=args.metrics,
        )

        for metric in args.metrics:
            raw_table = generate_diagnostic_metrics_table(raw_results[metric], metric)
            raw_tables.append(raw_table)
            raw_headings.append(f"Raw {metric.capitalize()}")
            raw_summaries.append(
                f"This table summarizes the raw {metric} of variant calls."
            )
            initial_metric_types.append(metric)

            # Export raw results to CSV
            raw_csv_output = f"{args.prefix}_{args.engine}_raw_{metric}.csv"
            export_diagnostic_metrics_to_csv(raw_table, raw_csv_output)

    # Process curated VCF comparisons if provided
    if args.curated_files:
        curated_results = process_diagnostic_metrics(
            file_paths=args.curated_files,
            data_type=args.engine,
            tp_method=args.tp_method,
            metrics=args.metrics,
        )

        for metric in args.metrics:
            curated_table = generate_diagnostic_metrics_table(
                curated_results[metric], metric
            )
            curated_tables.append(curated_table)
            curated_headings.append(f"Curated {metric.capitalize()}")
            curated_summaries.append(
                f"This table summarizes the curated {metric} of variant calls."
            )
            initial_metric_types.append(metric)

            # Export curated results to CSV
            curated_csv_output = f"{args.prefix}_{args.engine}_curated_{metric}.csv"
            export_diagnostic_metrics_to_csv(curated_table, curated_csv_output)

    # Combine tables in desired order
    tables: list[pd.DataFrame] = []
    headings: list[str] = []
    summaries: list[str] = []
    final_metric_types: list[DiagnosticMetricType] = []

    if args.raw_files and args.curated_files:
        # Interleave raw and curated tables by metric
        for i in range(len(args.metrics)):
            if i < len(raw_tables):
                tables.append(raw_tables[i])
                headings.append(raw_headings[i])
                summaries.append(raw_summaries[i])
                final_metric_types.append(initial_metric_types[i])
            if i < len(curated_tables):
                tables.append(curated_tables[i])
                headings.append(curated_headings[i])
                summaries.append(curated_summaries[i])
                final_metric_types.append(initial_metric_types[i])
    else:
        # Use whichever set of tables exists
        tables = raw_tables if args.raw_files else curated_tables
        headings = raw_headings if args.raw_files else curated_headings
        summaries = raw_summaries if args.raw_files else curated_summaries
        final_metric_types = initial_metric_types

    # Export results to markdown and word formats
    export_diagnostic_metrics_to_markdown(
        tables,
        f"{output_prefix}.md",
        final_metric_types,
        headings=headings,
        summaries=summaries,
    )
    export_diagnostic_metrics_to_word(
        tables,
        f"{output_prefix}.docx",
        final_metric_types,
        headings=headings,
        summaries=summaries,
    )


if __name__ == "__main__":
    main()
