#!/usr/bin/env python3
"""
Convert multi-sample VCF file to a folder of single sample VCF files.

Usage:
    convert_multi_sample_vcf --input-vcf=<PATH_TO_VCF> --output-folder=<NEW_FOLDER_NAME>
"""

import argparse
import gzip
from pathlib import Path

import pandas as pd

CONSTANT_FIELDS = [
    "#CHROM",
    "POS",
    "REF",
    "ALT",
    "ID",
    "QUAL",
    "FILTER",
    "INFO",
    "FORMAT",
]


def get_empty_format(format_line: str) -> str:
    """Return empty FORMAT field (e.g. 'GT:AD:DP' -> '.:.:.')."""
    return ":".join("." * len(format_line.split(":")))


def parse_file(input_file_path: Path) -> tuple[list[str], pd.DataFrame]:
    """Parse multi-sample VCF. Returns meta-info lines and DataFrame of variants."""
    info_lines: list[str] = []
    if input_file_path.suffix == ".gz":
        file = gzip.open(input_file_path, "rt")
    else:
        file = open(input_file_path, "r")

    for line in file:
        if line.startswith("##"):
            info_lines.append(line.strip())
        elif line.startswith("#CHROM"):
            header_line = line.strip().split("\t")
            break

    df = pd.read_csv(
        input_file_path, comment="#", sep="\t", header=None, names=header_line
    )
    return info_lines, df


def write_file(
    info_header: list[str], df: pd.DataFrame, output_location: Path, file_suffix: str
) -> None:
    """Write one single-sample VCF file per sample column.

    Args:
        info_header: VCF meta headers ('##')
        df: DataFrame with variant/sample columns
        output_location: Output directory
        file_suffix: Extra output filename suffix
    """
    identifiers = [col for col in df.columns if col not in CONSTANT_FIELDS]
    empty_format = get_empty_format(df.iloc[0]["FORMAT"])
    for identifier in identifiers:
        single_df = df[(df[identifier] != empty_format) & (df[identifier] != ".")]
        single_df = single_df.drop(
            columns=[item for item in identifiers if item != identifier]
        )
        file_name = (
            f"{output_location}/{identifier}.vcf"
            if not file_suffix
            else f"{output_location}/{identifier}.{file_suffix}.vcf"
        )
        with open(file_name, "w") as single_vcf:
            single_vcf.write("\n".join(info_header) + "\n")
            single_df.to_csv(single_vcf, sep="\t", index=False)
            single_vcf.close()


def main() -> None:
    """Split a multi-sample VCF into single-sample VCF files."""
    parser = argparse.ArgumentParser(
        description="Convert multi-sample VCF files into a folder of single-sample VCFs"
    )
    parser.add_argument("input_vcf", help="Path to the multi sample VCF")
    parser.add_argument(
        "-o",
        "--output-folder",
        required=True,
        help="Name of the single-sample VCFs folder",
    )
    parser.add_argument(
        "--suffix", required=False, default=None, help="Suffix for one sample VCF files"
    )

    args = parser.parse_args()
    input_file = Path(args.input_vcf)
    output_folder = Path(args.output_folder)
    output_folder.mkdir(exist_ok=True)
    file_suffix = args.suffix

    info_header, multi_df = parse_file(input_file)
    write_file(info_header, multi_df, args.output_folder, file_suffix)


if __name__ == "__main__":
    main()
