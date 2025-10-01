#!/usr/bin/env python3
"""
Reformat into a 4-column BED file and relabel 4th column such that it follows the format
<gene_symbol>_<refseq_accession>_<feature><exon_number>, where exon_number (if present) is
zero-padded dynamically:

For genes with <10 features: no leading zeros.
For 10-99 features: one leading zero (e.g. <feature>01).
For 100-999 features: two leading zeros (e.g. <feature>001).
Etc.

Usage:
    rename-bed-features -b <bed> -g <target_gene_list> -o <output_folder>
"""

import argparse
import gzip
import re
from enum import Enum
from pathlib import Path
from typing import IO, cast
import logging

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class FileMode(str, Enum):
    """Valid file modes."""

    READ = "r"
    WRITE = "w"


def open_file(filename: Path, mode: FileMode) -> IO[str]:
    """Opens file in the specified mode with the appropriate method depending on the extension."""
    if filename.suffix == ".gz":
        return cast(IO[str], gzip.open(filename, mode + "t"))
    else:
        return open(filename, mode)


def count_num_features(
    bed_file_path: Path, refseq_accession_regex_pattern: re.Pattern[str]
) -> dict[str, dict[str, int]]:
    """
    Parse input BED file and count the occurences of each feature type for each
    transcript (unique RefSeq accession) found in the attributes field.

    Args:
        bed_file_path: Path to input BED file.
        refseq_accession_regex_pattern: Compiled regex to extract RefSeq accession.

    Returns:
        Nested dict with structure {refseq_accession: {feature_type: count}}.

    Example:
        >>> result = count_num_features(bed_path, pattern)
        >>> result["NM_000760.4"]["exon"]
        17
    """
    transcript_feature_counts_dict: dict[str, dict[str, int]] = {}
    with open_file(bed_file_path, FileMode.READ) as in_bed:
        for line in in_bed:
            fields = line.split("\t")
            feature = fields[7]
            attributes = fields[9]

            # Get RefSeq accession
            refseq_attr_search = re.search(refseq_accession_regex_pattern, attributes)
            if refseq_attr_search:
                refseq_acc = refseq_attr_search.group(1)

                if refseq_acc not in transcript_feature_counts_dict.keys():
                    transcript_feature_counts_dict[refseq_acc] = {}
                if feature not in transcript_feature_counts_dict[refseq_acc].keys():
                    transcript_feature_counts_dict[refseq_acc][
                        feature
                    ] = 1  # initiate total count
                else:
                    transcript_feature_counts_dict[refseq_acc][
                        feature
                    ] += 1  # increment total count
    return transcript_feature_counts_dict


def construct_feature_name(
    gene_symbol: str,
    genomic_feature: str,
    bed_attributes: str,
    refseq_accession_regex_pattern: re.Pattern[str],
    transcript_feature_counts_dict: dict[str, dict[str, int]],
) -> str:
    """
    Construct updated feature name with the format:
    <gene_symbol>_<refseq_accession>_<genomic_feature><exon_number>.

    exon_number, if present, is dynamically zero-padded based on total number of genomic
    features present for the transcript.

    Args:
        gene_symbol: HGNC gene symbol.
        genomic_feature: Feature type.
        bed_attributes: Attributes field from BED file.
        refseq_accession_regex_pattern: Compiled regex to extract RefSeq accession.
        transcript_feature_counts_dict: Nested dict with feature counts for each RefSeq
            accession.

    Returns:
        Updated feature name.

    Raises:
        ValueError: If RefSeq accession is missing.
    """
    # Extract RefSeq accession
    refseq_attr_search = re.search(refseq_accession_regex_pattern, bed_attributes)
    if not refseq_attr_search:
        raise ValueError(
            f"RefSeq accession not found for {genomic_feature.upper()} feature "
            f"belonging to {gene_symbol}... skipping."
        )
    refseq_acc = refseq_attr_search.group(1)

    # Extract exon number, if applicable, and construct feature name
    # If no exon number, don't append to feature name
    exon_num_attr_search = re.search(r"exon_number.*(\d+)", bed_attributes)
    if exon_num_attr_search:
        exon_num = exon_num_attr_search.group(1)
        num_digits = len(
            str(transcript_feature_counts_dict[refseq_acc][genomic_feature])
        )
        exon_num_padded = str(exon_num).zfill(num_digits)
        feature_id = genomic_feature.upper() + exon_num_padded
    else:
        feature_id = genomic_feature.upper()

    return f"{gene_symbol}_{refseq_acc}_{feature_id}"


def main():
    parser = argparse.ArgumentParser(
        "Reformat input into a 4-column BED file and rename 4th column such that "
        "it follows the format "
        "<gene_symbol>_<refseq_accession>_<genomic_feature><exon_number>."
    )
    parser.add_argument(
        "-b", "--bed_file", help="Path to input BED file.", required=True
    )
    parser.add_argument(
        "-g",
        "--gene_list",
        help="Path to file with target HGNC gene symbols (one symbol per line).",
        required=True
    )
    parser.add_argument(
        "-A",
        "--attribute_key",
        help=(
            "Provided attribute is parsed to extract the RefSeq accession, "
            "which is used in the name field (fourth column)."
        ),
        default="db_xref",
    )
    parser.add_argument(
        "-o",
        "--output_folder",
        help="Name of folder to output renamed BED file.",
        required=True
    )

    # Parse args
    args = parser.parse_args()
    bed_file_path = Path(args.bed_file)
    gene_list_path = Path(args.gene_list)
    output_folder = Path(args.output_folder)
    output_folder.mkdir(exist_ok=True)

    # Define output bed filename based on input bed_file
    bed_ext_search = re.search(r"\.bed(\.gz)?$", args.bed_file)
    if bed_ext_search:
        ext = bed_ext_search.group(0)
        out_filename = bed_file_path.name.replace(ext, "") + ".renamed" + ext
    else:
        logging.error(
            "Improper input BED file detected - extension is neither "
            "`.bed` nor `.bed.gz`."
        )
        exit()

    # Parse gene_list file and store as target_gene_set
    target_gene_set = set()
    with open_file(gene_list_path, FileMode.READ) as target_gene_list:
        for line in target_gene_list:
            target_gene_set.add(line.strip())

    # First pass: get total count for each feature type per transcript
    refseq_accession_pattern = re.compile(rf"{args.attribute_key}.*(N[MRP]_\d+.\d+)")
    transcript_feature_counts_dict = count_num_features(
        bed_file_path, refseq_accession_pattern
    )

    # Second pass: update feature name (4th column)
    gene_set = set()  # keep track of genes that were in input_bed
    out_bed = open_file(output_folder / out_filename, FileMode.WRITE)
    with open_file(bed_file_path, FileMode.READ) as in_bed:
        for line in in_bed:
            fields = line.split("\t")
            chr = fields[0]
            start = fields[1]
            end = fields[2]
            feature_name = fields[3]
            genomic_feature = fields[7]
            attributes = fields[9]

            gene_set.add(feature_name)  # For logging purposes
            try:
                updated_feature_name = construct_feature_name(
                    feature_name,
                    genomic_feature,
                    attributes,
                    refseq_accession_pattern,
                    transcript_feature_counts_dict,
                )
                out_bed.write(f"{chr}\t{start}\t{end}\t{updated_feature_name}\n")
            except ValueError as e:
                logging.warning(e)
                continue
    out_bed.close()

    # Output warning if any genes in target gene list were not found in input BED file
    missing_genes = target_gene_set.difference(gene_set)
    if missing_genes:
        logging.warning(
            "One or more target genes were not found in input BED file: %s. "
            "Check whether these genes are stored as gene synonyms rather than "
            "gene symbols in MANE RefSeq GTF/GFF files.",
            ",".join(missing_genes),
        )


if __name__ == "__main__":
    main()
