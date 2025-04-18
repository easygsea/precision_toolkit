#!/usr/bin/env python3
"""
Count variants by size in a VCF file.

Usage:
    count_variants_by_size.py <vcf> [--size-stratification <size-stratification>...]
    [--count-occurrences]

Arguments:
    vcf: Path to the VCF file
    size-stratification: Size stratification points (e.g., 1 25 50)
    count-occurrences: Count variant occurrences in multi-sample VCF

Example Output:
    1: 200
    2-25: 25
    26-50: 2
    >50: 0
"""

import argparse

from clinical_tools.analysis.vcf import count_variants_by_size


def main():
    """Count variants by size in a VCF file.

    Args:
        vcf: Path to the VCF file
        size-stratification: Size stratification points (default: [1, 25, 49, 999])
        count-occurrences: Count variant occurrences in multi-sample VCFs

    Returns:
        Standard output with size ranges and counts
    """
    parser = argparse.ArgumentParser(
        description="Count variants by size in a VCF file."
    )
    parser.add_argument(
        "vcf",
        type=str,
        help="Path to the VCF file",
    )
    parser.add_argument(
        "-s",
        "--size-stratification",
        nargs="+",
        type=int,
        default=[1, 25, 49, 999],
        help="Size stratification points (e.g., 1 25 49 999)",
    )
    parser.add_argument(
        "-c",
        "--count-occurrences",
        action="store_true",
        help="Count each variant by its occurrences in multi-sample VCF",
    )
    args = parser.parse_args()

    counts = count_variants_by_size(
        args.vcf, args.size_stratification, args.count_occurrences
    )

    for size_range, count in counts.items():
        print(f"{size_range}: {count}")


if __name__ == "__main__":
    main()
