"""Analyze VCF files."""

import shutil
import tempfile
from enum import StrEnum
from pathlib import Path

import pysam
import pysam.bcftools


class BcftoolsIsecOutput(StrEnum):
    """Suffixes of output files produced by bcftools isec when comparing two VCF files.

    When intersecting two VCFs, bcftools isec yields four output files:
    - 0000.vcf: variants found only in vcf1
    - 0001.vcf: variants found only in vcf2
    - 0002.vcf: shared variants, as reported in vcf1
    - 0003.vcf: shared variants, as reported in vcf2
    """

    PRIVATE_TO_VCF1 = "0000"
    PRIVATE_TO_VCF2 = "0001"
    SHARED_FROM_VCF1 = "0002"
    SHARED_FROM_VCF2 = "0003"


def bgzip_and_index_vcf(vcf_path: Path) -> Path:
    """Return path to bgzipped and indexed VCF."""
    if not str(vcf_path).endswith(".vcf.gz"):
        bgzipped_vcf_path = Path(str(vcf_path).replace(".vcf", ".vcf.gz"))
        if not bgzipped_vcf_path.exists():
            pysam.tabix_compress(str(vcf_path), str(bgzipped_vcf_path))
    else:
        bgzipped_vcf_path = vcf_path

    vcf_tbi_path = Path(str(bgzipped_vcf_path) + ".tbi")
    if not vcf_tbi_path.exists():
        pysam.tabix_index(str(bgzipped_vcf_path), preset="vcf")

    return bgzipped_vcf_path


def collapse_multi_allelics(vcf_path: Path, collapsed_vcf_path: Path) -> None:
    """Collapse multi-allelic sites into a single record."""
    pysam.bcftools.norm(
        "--multiallelics",
        "+any",
        "--output",
        str(collapsed_vcf_path),
        "--output-type",
        "z",
        str(vcf_path),
        catch_stdout=False,
    )


def count_variants_by_size(
    vcf_file: str, size_stratification: list[int], count_occurrences: bool = False
) -> dict[str, int]:
    """Count variants by size in a VCF file.

    Args:
        vcf_file: Path to the VCF file
        size_stratification: List of stratification points, e.g. [1, 25, 49, 999]
        count_occurrences: Whether to count occurrences across samples

    Returns:
        Dictionary with size ranges as keys and counts as values
    """
    # Sort and deduplicate stratification points
    size_points = sorted(set(size_stratification))

    # Create size ranges
    size_ranges = []
    size_ranges.append(
        str(size_points[0]) if size_points[0] == 1 else f"1-{size_points[0]}"
    )
    for i in range(1, len(size_points)):
        size_ranges.append(f"{size_points[i - 1] + 1}-{size_points[i]}")
    size_ranges.append(f">{size_points[-1]}")

    size_counts = {range: 0 for range in size_ranges}

    with pysam.VariantFile(vcf_file) as vcf:

        def _process_variant(variant_size: int, occurrence_count: int) -> None:
            """Count variant in appropriate size range."""
            if variant_size <= size_points[0]:
                size_counts[size_ranges[0]] += occurrence_count
            else:
                found_range = False
                for i in range(1, len(size_points)):
                    if size_points[i - 1] < variant_size <= size_points[i]:
                        size_range = f"{size_points[i - 1] + 1}-{size_points[i]}"
                        size_counts[size_range] += occurrence_count
                        found_range = True
                if not found_range:
                    size_counts[f">{size_points[-1]}"] += occurrence_count

        def _get_occurrence_count(record: pysam.libcbcf.VariantRecord) -> int:
            """Calculate occurrence count."""
            if not count_occurrences or len(vcf.header.samples) <= 1:
                return 1
            else:
                return sum(
                    1
                    for sample in record.samples.values()
                    if sample[record.format.keys()[0]] not in (None, ".")
                )

        for record in vcf:
            if record.stop > record.pos:
                variant_size = record.stop - record.start
                _process_variant(variant_size, _get_occurrence_count(record))
            else:
                ref_len = len(record.ref) if record.ref and record.ref != "." else 0
                alt_len = (
                    len(record.alts[0]) if record.alts and record.alts[0] != "." else 0
                )
                variant_size = abs(ref_len - alt_len) + 1
                _process_variant(variant_size, _get_occurrence_count(record))

    return size_counts


def drop_genotypes(vcf_path: Path, sites_only_vcf_path: Path) -> None:
    """Drop sample columns yielding a sites-only VCF."""
    pysam.bcftools.view(
        "--drop-genotypes",
        "--output",
        str(sites_only_vcf_path),
        "--output-type",
        "z",
        str(vcf_path),
        catch_stdout=False,
    )


def extract_biallelic_snps(vcf_path: Path, biallelic_snps_vcf_path: Path) -> None:
    """Filter for bi-allelic SNPs only."""
    pysam.bcftools.view(
        "--types",
        "snps",
        "--min-alleles",
        "2",
        "--max-alleles",
        "2",
        "--output",
        str(biallelic_snps_vcf_path),
        "--output-type",
        "z",
        str(vcf_path),
        catch_stdout=False,
    )


def filter_vcf(
    vcf_path: Path, include_expression: str, filtered_vcf_path: Path
) -> None:
    """Filter for variants that satisfy the specified expression."""
    pysam.bcftools.filter(
        "--include",
        include_expression,
        "--output",
        str(filtered_vcf_path),
        "--output-type",
        "z",
        str(vcf_path),
        catch_stdout=False,
    )


def intersect_vcfs(
    vcf1_path: Path,
    vcf2_path: Path,
    keep: BcftoolsIsecOutput,
    intersected_vcf_path: Path,
) -> Path:
    """Intersect two VCFs, keeping either shared or private records as specified.

    Args:
        vcf1_path: Path to first VCF.
        vcf2_path: Path to second VCF.
        keep: BcftoolsIsecOutput value specifying which isec output file to keep.
        intersected_vcf_path: Path to output intersected VCF.

    Returns:
        Path to intersected VCF.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pysam.bcftools.isec(
            "--prefix",
            str(tmpdir),
            str(bgzip_and_index_vcf(vcf1_path)),
            str(bgzip_and_index_vcf(vcf2_path)),
            catch_stdout=False,
        )

        vcf_to_keep = Path(tmpdir) / f"{keep}.vcf"  # isec doesn't output bgzipped VCFs
        if str(intersected_vcf_path).endswith(".vcf.gz"):
            shutil.copy2(bgzip_and_index_vcf(vcf_to_keep), intersected_vcf_path)
        else:
            shutil.copy2(vcf_to_keep, intersected_vcf_path)

    return intersected_vcf_path
