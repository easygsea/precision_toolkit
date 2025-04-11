#!/usr/bin/env python3
"""
Convert multi-sample VCF file to a folder of single sample VCF files.

Usage:
    convert_multi_sample_vcf --input-vcf=<PATH_TO_VCF> --output-folder=<NEW_FOLDER_NAME>
"""

import argparse
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


def parse_file(input_file_path: Path) -> tuple[list[str], pd.DataFrame]:
    """
    Parse the multi sample vcf file and converts into a pandas dataframe.

    Args:
        input_file_path: path to the multi sample VCF file

    Returns:
        info_lines: header lines in the beginning of the VCF file
        header_line: line containing all the headers including the identifiers
        df: pandas DataFrame containing the sample information

    """
    info_lines: list[str] = []
    with open(input_file_path, "r") as vcf_file:
        for line in vcf_file:
            if line.startswith("##"):
                info_lines.append(line.strip())
            elif line.startswith("#CHROM"):
                header_line = line.strip().split("\t")
                break

    df = pd.read_csv(
        input_file_path, comment="#", sep="\t", header=None, names=header_line
    )
    return info_lines, df


def write_file(info_header: list[str], df: pd.DataFrame, output_location: Path) -> None:
    """
    Write individual samples to respective file in the output location.

    Args:
        info_header: info header lines in the original VCF file
        df: dataframe capturing all the information in the original file
        output_location: output directory as specified by the user

    Returns:
        None, but writes to files in the output directory
    """
    identifiers = [col for col in df.columns if col not in CONSTANT_FIELDS]
    for identifier in identifiers:
        single_df = df[df[identifier] != "."]
        single_df = single_df.drop(
            columns=[item for item in identifiers if item != identifier]
        )
        with open(f"{output_location}/{identifier}.vcf", "w") as single_vcf:
            single_vcf.write("\n".join(info_header) + "\n")
            single_df.to_csv(single_vcf, sep="\t", index=False)
            single_vcf.close()


def main():
    """
    Parse the original VCF and split into single-sample VCF files with each sample.

    Returns:
        None, modifies the output directory
    """
    parser = argparse.ArgumentParser(
        description="Convert multi-sample VCF files into a folder of single-sample VCFs"
    )
    parser.add_argument(
        "--input-vcf", required=True, help="Path to the multi sample VCF"
    )
    parser.add_argument(
        "--output-folder", required=True, help="Name of the single-sample VCFs folder"
    )

    args = parser.parse_args()
    input_file = args.input_vcf
    output_folder = Path(args.output_folder)
    output_folder.mkdir(exist_ok=True)

    info_header, multi_df = parse_file(input_file)
    write_file(info_header, multi_df, args.output_folder)


if __name__ == "__main__":
    main()
