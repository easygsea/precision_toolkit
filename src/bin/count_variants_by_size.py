#!/usr/bin/env python3
"""
Count variants by size in a VCF file or folder of VCF files.

Usage:
    count_variants_by_size.py <input_path> [--size-stratification <size>...]
    [--count-occurrences]

Arguments:
    input_path: Path to the VCF file or folder containing VCF files
    size-stratification: Size stratification points (e.g., 1 25 50)
    count-occurrences: Count variant occurrences in multi-sample VCF

Example Output:
    1: 200
    2-25: 25
    26-50: 2
    >50: 0
"""

import argparse
from pathlib import Path

from clinical_tools.analysis.vcf import count_variants_by_size


def main():
    """Count variants by size in a VCF file or folder of VCF files.

    Args:
        input_path: Path to the VCF file or folder containing VCF files
        size-stratification: Size stratification points (default: [1, 25, 49, 999])
        count-occurrences: Count variant occurrences in multi-sample VCFs

    Returns:
        Standard output with size ranges and counts
    """
    parser = argparse.ArgumentParser(
        description="Count variants by size in a VCF file or folder of VCF files."
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the VCF file or folder containing VCF files",
    )
    parser.add_argument(
        "-s",
        "--size-stratification",
        nargs="+",
        type=int,
        default=[1, 25, 49, 999],
        help="Size stratification points (default: 1 25 49 999)",
    )
    parser.add_argument(
        "-c",
        "--count-occurrences",
        action="store_true",
        help="Count each variant by its occurrences in multi-sample VCF",
    )
    args = parser.parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input path {input_path} does not exist")

    if any(size < 1 for size in args.size_stratification):
        raise ValueError("Size stratification points must be positive integers")

    if input_path.is_file():
        all_counts = count_variants_by_size(
            input_path, sorted(args.size_stratification), args.count_occurrences
        )
        for size_range, count in all_counts.items():
            print(f"{size_range}: {count}")
    elif input_path.is_dir():
        all_counts = {}
        vcf_files = list(input_path.glob("*.vcf"))
        num_files = len(vcf_files)

        for vcf_file in vcf_files:
            print(f"\nProcessing {vcf_file.name}:")
            counts = count_variants_by_size(
                vcf_file, args.size_stratification, args.count_occurrences
            )
            for size_range, count in counts.items():
                print(f"{size_range}: {count}")
                all_counts[size_range] = all_counts.get(size_range, 0) + count

        if all_counts:
            print(
                f"\nTotal counts across {num_files} VCF "
                f"file{'s' if num_files != 1 else ''}:"
            )
            for size_range, count in all_counts.items():
                print(f"{size_range}: {count}")
    else:
        raise ValueError(f"{input_path} is not a file or directory")


if __name__ == "__main__":
    main()
