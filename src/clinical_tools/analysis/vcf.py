"""Analyze VCF files."""

import pysam


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
