#!/usr/bin/env python3
import argparse
from clinical_tools.analysis.compute_variant_metrics import process_variant_metrics
from clinical_tools.render.concordance import (
    save_concordance_markdown,
    save_concordance_word,
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
        "--md-output",
        default="variant_concordance_results.md",
        help="Output Markdown file (default: variant_concordance_results.md).",
    )
    parser.add_argument(
        "--docx-output",
        default="variant_concordance_results.docx",
        help="Output Word file (default: concordance_results.docx).",
    )
    args = parser.parse_args()

    concordance_results = process_variant_metrics(
        file_paths=args.files, data_type=args.type
    )

    save_concordance_markdown(concordance_results, args.md_output)
    save_concordance_word(concordance_results, args.docx_output)


if __name__ == "__main__":
    main()
