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
    generate-standardized-bed --bed-file <bed> --output-folder <output_folder>
    [--attribute-key <refseq_accession_attribute_key>]
    [--features <comma_separated_feature_list>] [--gene-list <target_gene_file>]
    [--extend-cds-to-stop] [--include-utrs] [--output-introns] [--zero-pad-names]
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

VALID_FEATURES = {"CDS", "exon", "gene", "start_codon", "stop_codon", "transcript"}


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
    """Class for tracking a transcript's feature counts and ranges."""

    refseq_accession: str
    strand: Strand
    feature_counts: dict[str, int] = field(default_factory=dict)
    exons: list[GenomicRange] = field(default_factory=list)
    introns: list[GenomicRange] | None = None
    exon_to_intron: dict[tuple[int, int], GenomicRange] = field(default_factory=dict)
    exon_to_coding_exon: dict[tuple[int, int], GenomicRange] = field(
        default_factory=dict
    )
    start_codon: GenomicRange | None = None
    stop_codon: GenomicRange | None = None

    def calc_intron_ranges(self, exon_ranges: list[GenomicRange]) -> None:
        """
        Calculate introns based on provided exon ranges.

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
        if len(exon_ranges) > 1:
            # Sort exon GenomicRange objects by start position in range attribute
            sorted_exons = sorted(exon_ranges, key=lambda e: e.range[0])

            for i in range(len(sorted_exons) - 1):
                prev_exon = sorted_exons[i]
                next_exon = sorted_exons[i + 1]
                intron_start = prev_exon.range[1]
                intron_end = next_exon.range[0]

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

    def exclude_noncoding_exons(self) -> None:
        """
        Exclude and/or trim exons to remove non-coding portions (i.e. UTRs).

        exon_to_coding_exon attribute is populated with a 1-to-1 mapping of exon range
        to coding exon GenomicRange object.

        Example:
            >> transcript.exons
            [GenomicRange((100, 200), "1"), GenomicRange((300, 400), "2")]
            >> transcript.start_codon
            GenomicRange((150, 153), "1")
            >> transcript.stop_codon
            GenomicRange((350, 353), "2")
            >> transcript.exclude_noncoding_exons()
            >> transcript.exon_to_coding_exon
            {(100, 200): GenomicRange((150, 200), "1"),
             (300, 400): GenomicRange((300, 353), "2")}
        """
        if not self.start_codon or not self.stop_codon:
            logging.warning(
                f"Transcript {self.refseq_accession} missing start and/or "
                f"stop codon information, thus cannot determine non-coding "
                f"portions of exon... skipping exclusion of UTRs."
            )
            return

        if self.strand == Strand.PLUS:
            leftmost_codon = self.start_codon
            rightmost_codon = self.stop_codon
        else:
            leftmost_codon = self.stop_codon
            rightmost_codon = self.start_codon

        for exon in self.exons:
            # Full exon is in UTR, exclude
            if (
                exon.range[1] < leftmost_codon.range[0]
                or exon.range[0] > rightmost_codon.range[1]
            ):
                continue
            else:
                # Update exon coordinates if stop/start codon in exon
                coding_exon_start = exon.range[0]
                coding_exon_end = exon.range[1]
                if exon.number_attribute == leftmost_codon.number_attribute:
                    coding_exon_start = leftmost_codon.range[0]
                if exon.number_attribute == rightmost_codon.number_attribute:
                    coding_exon_end = rightmost_codon.range[1]

                # Map exon range to coding exon range
                self.exon_to_coding_exon[exon.range] = GenomicRange(
                    (coding_exon_start, coding_exon_end), exon.number_attribute
                )


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
    bed_file_path: Path,
    refseq_accession_regex_pattern: re.Pattern[str],
    target_genes: set[str],
) -> tuple[dict[str, Transcript], set[str]]:
    """
    Parse input BED file to track feature counts and genomic ranges per transcript.

    Args:
        bed_file_path: Path to input BED file.
        refseq_accession_regex_pattern: Compiled regex to extract RefSeq accession.
        target_genes: Set of target gene symbols to filter for. If empty, all genes
            are included.

    Returns:
        Tuple containing:
            - Dictionary mapping RefSeq accessions to corresponding Transcript objects,
              which tracks feature counts and genomic ranges.
            - Set of gene symbols found in input BED file.
    """
    refseq_accession_to_transcript_obj: dict[str, Transcript] = {}
    gene_set = set()  # keep track of genes that were in input_bed
    with open_file(bed_file_path, FileMode.READ) as in_bed:
        for line in in_bed:
            fields = line.split("\t")
            start = int(fields[1])
            end = int(fields[2])
            feature_name = fields[3]
            strand = fields[5]
            feature = fields[7]
            attributes = fields[9]

            # Get RefSeq accession
            refseq_acc = extract_refseq_accession(
                refseq_accession_regex_pattern, attributes
            )
            if refseq_acc is not None:
                # Skip features not in target_genes, if applicable
                if target_genes and feature_name not in target_genes:
                    continue

                gene_set.add(feature_name)  # for logging purposes

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
                exon_number = extract_exon_number(attributes)
                if feature == "exon":
                    transcript_obj.exons.append(GenomicRange((start, end), exon_number))
                elif feature == "start_codon":
                    transcript_obj.start_codon = GenomicRange((start, end), exon_number)
                elif feature == "stop_codon":
                    transcript_obj.stop_codon = GenomicRange((start, end), exon_number)

    return refseq_accession_to_transcript_obj, gene_set


def construct_feature_name(
    gene_symbol: str,
    genomic_feature: str,
    refseq_acc: str | None,
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
        if zero_pad_names and refseq_acc:
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

    if refseq_acc is None:
        logging.warning(
            f"RefSeq accession not found for {genomic_feature.upper()} feature "
            f"belonging to {gene_symbol}... standardized name won't "
            f"include RefSeq accession."
        )
        return f"{gene_symbol}_{feature_id}"
    else:
        return f"{gene_symbol}_{refseq_acc}_{feature_id}"


def get_corresponding_intron(
    exon_range: tuple[int, int], exon_to_intron: dict[tuple[int, int], GenomicRange]
) -> GenomicRange | None:
    """Get corresponding intron for provided exon range."""
    if exon_range in exon_to_intron.keys():
        return exon_to_intron[exon_range]

    # Attempt to perform "fuzzy" search to account for trimmed exons (i.e. UTR
    # exclusion)
    for exon in exon_to_intron.keys():
        if exon_range[0] <= exon[1] and exon[0] <= exon_range[1]:
            return exon_to_intron[exon]

    # No corresponding intron
    return None


def trim_utr_exon(
    transcript_obj: Transcript, exon_range: tuple[int, int]
) -> GenomicRange | None:
    """Exclude non-coding exons or non-coding regions of exons."""
    # Calculate coding exon coordinates if not done previously
    if not transcript_obj.exon_to_coding_exon:
        transcript_obj.exclude_noncoding_exons()
    exon_to_coding_exon = transcript_obj.exon_to_coding_exon

    # Check if exon is a coding exon, if so return exon with non-coding
    # regions trimmed (when applicable)
    if exon_range in exon_to_coding_exon.keys():
        return exon_to_coding_exon[exon_range]
    else:
        return None  # UTR-only exon, exclude


def generate_modified_target_bed(
    bed_file_path: Path,
    target_genes: set[str],
    target_features: list[str],
    refseq_accession_regex_pattern: re.Pattern[str],
    refseq_accession_to_transcript_obj: dict[str, Transcript],
    out_bed_file_path: Path,
    extend_cds_to_stop: bool,
    include_utrs: bool,
    output_introns: bool,
    zero_pad_names: bool,
) -> None:
    """
    Standardize BED features with optional boundary adjustments.

    Optional boundary adjustment apply to exon and CDS features. Introns may also be
    derived from exon features and output.

    Args:
        bed_file_path: Path to input BED file.
        target_genes: Set of target gene symbols to filter for. If empty, all
            genes are included.
        target_features: List of features to filter for.
        refseq_accession_regex_pattern: Compiled regex to extract RefSeq accession.
        refseq_accession_to_transcript_obj: Dictionary mapping RefSeq accessions to
            corresponding Transcript objects.
        out_bed_file_path: Path to output standardized BED file.
        extend_cds_to_stop: If True, extend CDS features to include stop codons.
        include_utrs: If True, do not exclude/trim UTRs from exons.
        output_introns: If True, calculate introns and output to target BED file.

    Returns:
        None, standardized BED file is written to out_bed_file_path.
    """
    out_bed = open_file(out_bed_file_path, FileMode.WRITE)
    with open_file(bed_file_path, FileMode.READ) as in_bed:
        for line in in_bed:
            fields = line.strip().split("\t")
            chr = fields[0]
            start = fields[1]
            end = fields[2]
            feature_name = fields[3]
            genomic_feature = fields[7]
            attributes = fields[9]
            exon_num = extract_exon_number(attributes)

            # Skip feature if not in target_genes
            if target_genes and feature_name not in target_genes:
                continue

            # Extract refseq accession
            refseq_acc = extract_refseq_accession(
                refseq_accession_regex_pattern, attributes
            )

            updated_feature_name = construct_feature_name(
                feature_name,
                genomic_feature,
                refseq_acc,
                exon_num,
                refseq_accession_to_transcript_obj,
                zero_pad_names,
            )

            # Apply flags
            # Default to original coordinates
            out_bed_entries = []
            out_bed_entries.append(
                (genomic_feature, f"{chr}\t{start}\t{end}\t{updated_feature_name}\n")
            )
            if refseq_acc:
                transcript_obj = refseq_accession_to_transcript_obj[refseq_acc]

                # For CDS features, extend coordinates to include stop codon, if
                # applicable
                if genomic_feature == "CDS" and extend_cds_to_stop:
                    if not transcript_obj.stop_codon:
                        logging.warning(
                            f"Transcript {refseq_acc} missing stop codon "
                            f"information, thus cannot extend CDS to include "
                            f"stop codon... skipping extension."
                        )
                    elif exon_num == transcript_obj.stop_codon.number_attribute:
                        updated_start, updated_end = (int(start), int(end))
                        if transcript_obj.strand == Strand.PLUS:
                            updated_end = transcript_obj.stop_codon.range[1]
                        else:
                            updated_start = transcript_obj.stop_codon.range[0]
                        out_bed_entries = [
                            (
                                genomic_feature,
                                f"{chr}\t{updated_start}\t"
                                f"{updated_end}\t{updated_feature_name}\n",
                            )
                        ]

                elif genomic_feature == "exon":
                    exon_range = (int(start), int(end))

                    if not include_utrs:
                        coding_exon = trim_utr_exon(transcript_obj, exon_range)
                        if coding_exon:
                            out_bed_entries = [
                                (
                                    genomic_feature,
                                    f"{chr}\t{coding_exon.range[0]}\t"
                                    f"{coding_exon.range[1]}\t{updated_feature_name}\n",
                                )
                            ]
                        else:
                            continue  # skip UTR-only exon

                    if output_introns:
                        if "intron" not in target_features:
                            target_features.append("intron")

                        # Calculate introns if not done previously
                        if transcript_obj.introns is None:
                            if not include_utrs:
                                # Calculate introns based on coding exons
                                transcript_obj.calc_intron_ranges(
                                    list(transcript_obj.exon_to_coding_exon.values())
                                )
                            else:
                                transcript_obj.calc_intron_ranges(transcript_obj.exons)

                        # Check if transcript has introns (i.e. > 1 exon); if so, write
                        if transcript_obj.introns:
                            exon_to_intron = transcript_obj.exon_to_intron
                            exon_range = (int(start), int(end))
                            intron = get_corresponding_intron(
                                exon_range, exon_to_intron
                            )

                            if intron:
                                intron_feature_name = construct_feature_name(
                                    feature_name,
                                    "intron",
                                    refseq_acc,
                                    intron.number_attribute,
                                    refseq_accession_to_transcript_obj,
                                    zero_pad_names,
                                )
                                out_bed_entries.append(
                                    (
                                        "intron",
                                        f"{chr}\t{intron.range[0]}\t"
                                        f"{intron.range[1]}\t{intron_feature_name}\n",
                                    )
                                )

            # Skip feature if not in target_features
            # Filtering done last to ensure introns can be output independent of exons
            for entry in out_bed_entries:
                if entry[0] in target_features:
                    out_bed.write(entry[1])


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
        help=(
            "Path to file with target HGNC gene symbols (one symbol per line). "
            "If provided, warning is output for any genes in this list that "
            "are not found in input BED file."
        ),
    )
    parser.add_argument(
        "-A",
        "--attribute-key",
        help=(
            "Provided attribute is parsed to extract the RefSeq accession, "
            "which is used in the name field (fourth column)."
        ),
        default="transcript_id",
    )
    parser.add_argument(
        "-f",
        "--features",
        help=(
            "Comma-separated list of genomic features to include in target BED file."
        ),
    )
    parser.add_argument(
        "--extend-cds-to-stop",
        help=(
            "By definition, CDS does not include stop codons. Supplying this "
            "flag will extend CDS features to include the stop codon."
        ),
        action="store_true",
    )
    parser.add_argument(
        "--include-utrs",
        help=(
            "By default, only coding regions are included for each transcript "
            "in target BED file (i.e. exon features will be excluded or "
            "trimmed to exclude UTRs). Supplying this flag will disable this "
            "functionality."
        ),
        action="store_true",
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
    gene_list_path = Path(args.gene_list) if args.gene_list else None
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

    # Ensure valid features were provided
    if args.features:
        feature_list = [f.strip() for f in args.features.split(",")]
        invalid_features = set(feature_list) - VALID_FEATURES
        if invalid_features:
            logging.error(
                f"Invalid features provided to --features: "
                f"{','.join(invalid_features)}. Must be one of "
                f"{','.join(VALID_FEATURES)}."
            )
            exit()
    else:
        feature_list = list(VALID_FEATURES)

    # If gene_list provided, parse gene_list file and store as target_gene_set
    target_gene_set = set()
    if gene_list_path:
        with open_file(gene_list_path, FileMode.READ) as target_gene_list:
            for line in target_gene_list:
                target_gene_set.add(line.strip())

    # First pass: parse BED file to extract feature counts and genomic ranges per
    # transcript
    # Use non-greedy quantifier to match first RefSeq accession encountered after
    # args.attribute_key
    refseq_accession_pattern = re.compile(rf"{args.attribute_key}.*?(N[MRP]_\d+\.\d+)")
    refseq_accession_to_transcript_obj, gene_set = parse_bed_file(
        bed_file_path, refseq_accession_pattern, target_gene_set
    )

    # Second pass: generate target BED
    # Filter BED file for genes/features of interest and adjust exon/CDS
    # coordinates, if applicable
    generate_modified_target_bed(
        bed_file_path,
        target_gene_set,
        feature_list,
        refseq_accession_pattern,
        refseq_accession_to_transcript_obj,
        output_folder / out_filename,
        args.extend_cds_to_stop,
        args.include_utrs,
        args.output_introns,
        args.zero_pad_names,
    )

    # Output warning if introns are output but exons are not
    # Has been observed when CDS and intron features are output
    if args.output_introns and "exon" not in feature_list:
        logging.warning(
            "Output standardized BED file may not be in sorted order. Check before "
            "utilizing BED file in downstream applications.",
        )

    # If gene_list provided, output warning if any genes in target gene list
    # were not found in input BED file
    if target_gene_set:
        missing_genes = target_gene_set.difference(gene_set)
        if missing_genes:
            logging.warning(
                "One or more target genes were not found in input BED file: "
                "%s. Check whether these genes are stored as gene synonyms "
                "rather than gene symbols in MANE RefSeq GTF/GFF files.",
                ",".join(missing_genes),
            )


if __name__ == "__main__":
    main()
