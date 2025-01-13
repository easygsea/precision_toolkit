#!/usr/bin/env python3
import argparse
from clinical_tools.analysis.compute_variant_metrics import process_variant_metrics
from clinical_tools.render.concordance import (
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

    # Parse arguments first so we can use args.type
    args = parser.parse_args()

    # Now set the default filenames with the type argument
    parser.set_defaults(
        csv_output=f"variant_concordance_{args.type}.csv",
        md_output=f"variant_concordance_{args.type}.md",
        docx_output=f"variant_concordance_{args.type}.docx",
    )

    # Re-parse arguments to apply the new defaults
    args = parser.parse_args()

    # Generate the concordance table
    concordance_results = process_variant_metrics(
        file_paths=args.files, data_type=args.type
    )
    concordance_table = generate_concordance_table(concordance_results)

    # Export to different formats
    export_concordance_to_csv(concordance_table, args.csv_output)
    export_concordance_to_markdown(
        concordance_table,
        args.md_output,
        heading="Variant Concordance",
        summary="This table summarizes the concordance of variant calls.",
    )
    export_concordance_to_word(
        concordance_table,
        args.docx_output,
        heading="Variant Concordance",
        summary="This document summarizes the concordance of variant calls.",
    )


if __name__ == "__main__":
    main()
