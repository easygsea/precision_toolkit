#!/usr/bin/env python3
"""
Reformat BED6+4 to 4-column BED file with standardized feature names.

Updated names should follow the format
<gene_symbol>_<refseq_accession>_<feature><exon_number>, where exon_number
(if present) is optionally zero-padded dynamically:

For genes with <10 features: no leading zeros.
For 10-99 features: one leading zero (e.g. <feature>01).
For 100-999 features: two leading zeros (e.g. <feature>001).
Etc.

Usage:
    generate-standardized-bed --bed_file <bed> --gene_list <target_gene_file>
    --output_folder <output_folder> [--output_introns] [--zero-pad-names]
"""

import argparse
import gzip
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import IO, cast

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Strand(str, Enum):
    """Valid strand orientations."""

    PLUS = "+"
    MINUS = "-"
    UNSTRANDED = "."


@dataclass
class GenomicRange:
    """Class for tracking a genomic range and associated number attribute."""

    range: tuple
    number_attribute: str = ""


@dataclass
class Transcript:
    """Class for tracking a transcript's feature counts and exon/intron ranges."""

    refseq_accession: str
    strand: Strand
    feature_counts: dict[str, int] = field(default_factory=dict)
    exons: list[GenomicRange] = field(default_factory=list)
    introns: list[GenomicRange] | None = None
    exon_to_intron: dict[tuple[int, int], GenomicRange] = field(default_factory=dict)

    def calc_intron_ranges(self) -> None:
        """
        Calculate introns based on exon ranges.

        feature_counts attribute is updated to reflect new intron feature and
        exon_to_intron attribute is populated with a 1-to-1 mapping of exon range to
        intron GenomicRange object.

        Example:
            >> transcript.exons
            [GenomicRange((100, 200), "1"), GenomicRange((300, 400), "2")]
            >> transcript.calc_intron_ranges()
            >> transcript.introns
            [GenomicRange((201, 299), "1")]
            >> transcript.exon_to_intron
            {(100, 200): GenomicRange((201, 299), "1")}
        """
        self.introns = []
        if len(self.exons) > 1:
            # Sort exon GenomicRange objects by start position in range attribute
            sorted_exons = sorted(self.exons, key=lambda e: e.range[0])

            for i in range(len(sorted_exons) - 1):
                prev_exon = sorted_exons[i]
                next_exon = sorted_exons[i + 1]
                intron_start = prev_exon.range[1] + 1
                intron_end = next_exon.range[0] - 1

                # Determine which exon precedes intron based on strand
                if self.strand == Strand.MINUS:
                    intron_number = next_exon.number_attribute
                else:
                    intron_number = prev_exon.number_attribute

                # Create intron GenomicRange object and add to introns list
                intron = GenomicRange(
                    range=(intron_start, intron_end), number_attribute=intron_number
                )
                self.introns.append(intron)

                # Map exon range to intron range
                self.exon_to_intron[prev_exon.range] = intron

                # Update feature counts
                self.feature_counts["intron"] = len(self.introns)


class FileMode(str, Enum):
    """Valid file modes."""

    READ = "r"
    WRITE = "w"


def open_file(filename: Path, mode: FileMode) -> IO[str]:
    """Open file with the appropriate method depending on the extension."""
    if filename.suffix == ".gz":
        return cast(IO[str], gzip.open(filename, mode + "t"))
    else:
        return open(filename, mode)


def extract_refseq_accession(
    refseq_accession_regex_pattern: re.Pattern[str], bed_attributes: str
) -> str | None:
    """Extract RefSeq accession from BED attributes."""
    match = re.search(refseq_accession_regex_pattern, bed_attributes)
    return match.group(1) if match else None


def extract_exon_number(bed_attributes: str) -> str:
    """Extract exon number from BED attributes."""
    exon_num_attr_search = re.search(r"exon_number.*?(\d+)", bed_attributes)
    return exon_num_attr_search.group(1) if exon_num_attr_search else ""


def parse_bed_file(
    bed_file_path: Path, refseq_accession_regex_pattern: re.Pattern[str]
) -> dict[str, Transcript]:
    """
    Parse input BED file to track feature counts and genomic ranges per transcript.

    Args:
        bed_file_path: Path to input BED file.
        refseq_accession_regex_pattern: Compiled regex to extract RefSeq accession.

    Returns:
        Dictionary mapping RefSeq accessions to corresponding Transcript objects, which
        tracks feature counts and genomic ranges.
    """
    refseq_accession_to_transcript_obj: dict[str, Transcript] = {}
    with open_file(bed_file_path, FileMode.READ) as in_bed:
        for line in in_bed:
            fields = line.split("\t")
            start = int(fields[1])
            end = int(fields[2])
            strand = fields[5]
            feature = fields[7]
            attributes = fields[9]

            # Get RefSeq accession
            refseq_acc = extract_refseq_accession(
                refseq_accession_regex_pattern, attributes
            )
            if refseq_acc is not None:
                # Create transcript object, if not already present
                if refseq_acc not in refseq_accession_to_transcript_obj.keys():
                    refseq_accession_to_transcript_obj[refseq_acc] = Transcript(
                        refseq_acc, Strand(strand)
                    )
                transcript_obj = refseq_accession_to_transcript_obj[refseq_acc]

                # Update feature count attribute
                if feature not in transcript_obj.feature_counts.keys():
                    # Initiate total count
                    transcript_obj.feature_counts[feature] = 1
                else:
                    # Increment total count
                    transcript_obj.feature_counts[feature] += 1

                # Update exon attribute, if applicable
                if feature == "exon":
                    exon_number = extract_exon_number(attributes)
                    transcript_obj.exons.append(GenomicRange((start, end), exon_number))

    return refseq_accession_to_transcript_obj


def construct_feature_name(
    gene_symbol: str,
    genomic_feature: str,
    refseq_acc: str,
    exon_num: str,
    refseq_accession_to_transcript_obj: dict[str, Transcript],
    zero_pad_names: bool,
) -> str:
    """
    Construct updated feature name.

    Feature names follow the format
    <gene_symbol>_<refseq_accession>_<genomic_feature><exon_number> where exon_number,
    if present, is dynamically zero-padded based on total number of genomic features
    present for the transcript.

    Args:
        gene_symbol: HGNC gene symbol.
        genomic_feature: Feature type.
        refseq_acc: RefSeq accession.
        exon_num: Exon number extracted from BED attributes.
        refseq_accession_to_transcript_obj: Dictionary mapping RefSeq accessions to
            corresponding Transcript objects.
        zero_pad_names: If True, zero-pad numbers in feature names (e.g., exon_001
            instead of exon_1).

    Returns:
        Updated feature name.
    """
    # Extract exon number, if applicable, and construct feature name
    # If no exon number, don't append to feature name
    if exon_num:
        if zero_pad_names:
            num_digits = len(
                str(
                    refseq_accession_to_transcript_obj[refseq_acc].feature_counts[
                        genomic_feature
                    ]
                )
            )
            exon_num_padded = (
                exon_num.zfill(num_digits) if len(exon_num) < num_digits else exon_num
            )
        else:
            # No padding required
            exon_num_padded = exon_num
        feature_id = genomic_feature.upper() + exon_num_padded
    else:
        feature_id = genomic_feature.upper()

    return f"{gene_symbol}_{refseq_acc}_{feature_id}"


def main() -> None:
    """
    Reformat BED file and rename features.

    Returns:
        Modified BED file.
    """
    parser = argparse.ArgumentParser(
        "Reformat input into a 4-column BED file and rename 4th column such that "
        "it follows the format "
        "<gene_symbol>_<refseq_accession>_<genomic_feature><exon_number>."
    )
    parser.add_argument(
        "-b", "--bed-file", help="Path to input BED file.", required=True
    )
    parser.add_argument(
        "-g",
        "--gene-list",
        help="Path to file with target HGNC gene symbols (one symbol per line).",
        required=True,
    )
    parser.add_argument(
        "-A",
        "--attribute-key",
        help=(
            "Provided attribute is parsed to extract the RefSeq accession, "
            "which is used in the name field (fourth column)."
        ),
        default="db_xref",
    )
    parser.add_argument(
        "--output-introns",
        help="Calculate introns and output to reformatted BED file.",
        action="store_true",
    )
    parser.add_argument(
        "--zero-pad-names",
        help="Dynamically add zeros to exon_number in feature names.",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        help="Name of folder to output reformatted BED file.",
        required=True,
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
        out_filename = bed_file_path.name.replace(ext, "") + ".reformatted" + ext
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

    # First pass: parse BED file to extract feature counts and genomic ranges per
    # transcript
    refseq_accession_pattern = re.compile(rf"{args.attribute_key}.*(N[MRP]_\d+.\d+)")
    refseq_accession_to_transcript_obj = parse_bed_file(
        bed_file_path, refseq_accession_pattern
    )

    # Second pass: reformat BED file, update feature name (4th column), and add introns
    # if applicable
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
            exon_num = extract_exon_number(attributes)

            # Extract refseq accession
            refseq_acc = extract_refseq_accession(refseq_accession_pattern, attributes)
            if refseq_acc is None:
                logging.warning(
                    f"RefSeq accession not found for {genomic_feature.upper()} feature "
                    f"belonging to {feature_name}... skipping."
                )
                continue

            gene_set.add(feature_name)  # For logging purposes
            updated_feature_name = construct_feature_name(
                feature_name,
                genomic_feature,
                refseq_acc,
                exon_num,
                refseq_accession_to_transcript_obj,
                args.zero_pad_names,
            )
            out_bed.write(f"{chr}\t{start}\t{end}\t{updated_feature_name}\n")

            # If current line in BED file is an exon feature write corresponding intron
            # feature to BED file, if applicable
            if args.output_introns and genomic_feature == "exon":
                transcript_obj = refseq_accession_to_transcript_obj[refseq_acc]
                # Calculate intron ranges if first time encountering an exon for
                # transcript
                if transcript_obj.introns is None:
                    transcript_obj.calc_intron_ranges()

                # Check if transcript has introns (i.e. more than one exon) and write
                if transcript_obj.introns:
                    exon_to_intron = transcript_obj.exon_to_intron
                    exon_range = (int(start), int(end))

                    if exon_range in exon_to_intron.keys():
                        # Get corresponding intron and construct intron feature name
                        intron = exon_to_intron[exon_range]
                        intron_feature_name = construct_feature_name(
                            feature_name,
                            "intron",
                            refseq_acc,
                            intron.number_attribute,
                            refseq_accession_to_transcript_obj,
                            args.zero_pad_names,
                        )
                        out_bed.write(
                            f"{chr}\t{intron.range[0]}\t{intron.range[1]}\t"
                            f"{intron_feature_name}\n"
                        )

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
