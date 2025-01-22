#!/usr/bin/env python3
import argparse
from clinical_tools.analysis.compute_variant_metrics import process_variant_metrics
from clinical_tools.render.variant_concordance import (
    generate_concordance_table,
    export_concordance_to_csv,
    export_concordance_to_markdown,
    export_concordance_to_word,
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compute combined variant metrics across samples from hap.py or "
            "witty.er output files."
        )
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["happy", "wittyer"],
        required=True,
        help="Type of files to process: 'happy' or 'wittyer'.",
    )
    parser.add_argument(
        "-f", "--files", nargs="+", required=True, help="List of file paths to process."
    )
    parser.add_argument(
        "-p",
        "--prefix",
        default="variant_concordance",
        help="Prefix for output filenames. Default is 'variant_concordance'."
    )

    # Parse arguments first so we can use args.type
    args = parser.parse_args()

    # Generate the concordance table
    concordance_results = process_variant_metrics(
        file_paths=args.files, data_type=args.type
    )
    concordance_table = generate_concordance_table(concordance_results)

    # Define output filenames with the given prefix
    csv_output = f"{args.prefix}_{args.type}.csv"
    md_output = f"{args.prefix}_{args.type}.md"
    docx_output = f"{args.prefix}_{args.type}.docx"
    
    # Export to different formats
    export_concordance_to_csv(concordance_table, csv_output)
    export_concordance_to_markdown(
        concordance_table,
        md_output,
        heading="Variant Concordance",
        summary="This table summarizes the concordance of variant calls.",
    )
    export_concordance_to_word(
        concordance_table,
        docx_output,
        heading="Variant Concordance",
        summary="This document summarizes the concordance of variant calls.",
    )


if __name__ == "__main__":
    main()