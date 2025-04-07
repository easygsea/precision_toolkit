#!/usr/bin/env python3
"""
Convert multi-sample VCF file to a folder of single sample VCF files.

Usage:
    convert_multi_sample_vcf --input-vcf=<PATH_TO_VCF> --output-folder=<NEW_FOLDER_NAME>
"""

import argparse
import os

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


def parse_file(input_file_path: str) -> tuple[list[str], list[str], pd.DataFrame]:
    """
    Parse the multi sample vcf file and converts into a pandas dataframe.

    Args:
        input_file_path - path to the multi sample VCF file

    Returns:
        info_lines - header lines in the beginning of the VCF file
        header_line - line containing all the headers including the identifiers
        df - pandas DataFrame containing the sample information

    """
    data = []
    info_lines = []
    with open(input_file_path, "r") as vcf_file:
        for lines in vcf_file:
            for line in lines.split("\n"):
                if line[:2] == "##":
                    info_lines.append(line)
                elif line[:6] == "#CHROM":
                    header_line = line.split("\t")
                else:
                    data_line = line.split("\t")
                    if line[0] != "":
                        data.append(data_line)

    df = pd.DataFrame(data, columns=header_line)
    return info_lines, header_line, df


def write_file(info_header: list[str], df: pd.DataFrame, output_location: str) -> None:
    """
    Write individual samples to respective file in the output location.

    Args:
        info_header: info header lines in the original VCF file
        df: dataframe capturing all the information in the original file
        output_location: output directory as specified by the user

    Returns:
        None, but writes to files in the output directory
    """
    identifiers = [
        identifier
        for identifier in df.columns.tolist()
        if identifier not in CONSTANT_FIELDS
    ]
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-vcf", required=True, help="Path to the multi sample VCF"
    )
    parser.add_argument(
        "--output-folder", required=True, help="Name of the single-sample VCFs folder"
    )

    args = parser.parse_args()
    input_file = args.input_vcf
    os.mkdir(args.output_folder)

    info_header, columns, multi_df = parse_file(input_file)
    write_file(info_header, multi_df, args.output_folder)


if __name__ == "__main__":
    main()
