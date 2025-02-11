#!/usr/bin/env python3
import argparse

from clinical_tools.analysis.compute_variant_metrics import process_variant_metrics
from clinical_tools.core.constants import VariantConcordanceEngine
from clinical_tools.render.variant_concordance import (
    export_concordance_to_csv,
    export_concordance_to_markdown,
    export_concordance_to_word,
    generate_concordance_table,
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compute combined variant metrics across samples from hap.py or "
            "witty.er output files."
        )
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
        "-p",
        "--prefix",
        default="variant_concordance",
        help="Prefix for output filenames. Default is 'variant_concordance'.",
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
    tables = []
    headings = []
    summaries = []

    # Process raw variant concordance results if provided
    if args.raw_files:
        raw_concordance_results = process_variant_metrics(
            file_paths=args.raw_files, data_type=args.engine
        )
        raw_concordance_table = generate_concordance_table(raw_concordance_results)

        # Export raw results to CSV
        raw_csv_output = f"{args.prefix}_{args.engine}_raw.csv"
        export_concordance_to_csv(raw_concordance_table, raw_csv_output)

        # Add raw results to tables
        tables.append(raw_concordance_table)
        headings.append("Raw Variant Concordance")
        summaries.append("This table summarizes the raw concordance of variant calls.")

    # Process curated results if provided
    if args.curated_files:
        curated_concordance_results = process_variant_metrics(
            file_paths=args.curated_files, data_type=args.engine
        )
        curated_concordance_table = generate_concordance_table(
            curated_concordance_results
        )

        # Export curated results to CSV
        curated_csv_output = f"{args.prefix}_{args.engine}_curated.csv"
        export_concordance_to_csv(curated_concordance_table, curated_csv_output)

        # Add curated results to tables
        tables.append(curated_concordance_table)
        headings.append("Curated Variant Concordance")
        summaries.append(
            "This table summarizes the concordance of curated variant calls."
        )

    # Export results to markdown and word formats
    export_concordance_to_markdown(
        tables, f"{output_prefix}.md", headings=headings, summaries=summaries
    )
    export_concordance_to_word(
        tables, f"{output_prefix}.docx", headings=headings, summaries=summaries
    )


if __name__ == "__main__":
    main()
