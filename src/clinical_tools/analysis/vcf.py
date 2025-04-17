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
    for i in range(len(size_points)):
        if i == 0:
            size_ranges.append(str(size_points[i]))
        else:
            size_ranges.append(f"{size_points[i - 1] + 1}-{size_points[i]}")
    size_ranges.append(f">{size_points[-1]}")

    size_counts = {range: 0 for range in size_ranges}

    with pysam.VariantFile(vcf_file) as vcf:
        for record in vcf:
            ref_len = len(record.ref) if record.ref != "." else 0
            for alt in record.alts:
                alt_len = len(alt) if alt != "." else 0
                variant_size = abs(ref_len - alt_len) + 1

                # Calculate occurrence count for multi-sample VCF
                occurrence_count = 1
                if count_occurrences and len(vcf.header.samples) > 1:
                    occurrence_count = sum(
                        1
                        for sample in record.samples.values()
                        if sample["GT"] != (None, None)
                    )

                if variant_size == 0:
                    size_counts[str(size_points[0])] += occurrence_count
                elif variant_size == 1:
                    size_counts[str(size_points[0])] += occurrence_count
                else:
                    found_range = False
                    for i in range(1, len(size_points)):
                        if size_points[i - 1] < variant_size <= size_points[i]:
                            size_range = f"{size_points[i - 1] + 1}-{size_points[i]}"
                            size_counts[size_range] += occurrence_count
                            found_range = True
                            break
                    if not found_range:
                        size_counts[f">{size_points[-1]}"] += occurrence_count

    return size_counts
