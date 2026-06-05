"""
Plot allele frequencies of germline variants to assess sample contamination.

Usage:
    plot-contamination-vafs --variant-calls <dragen_tmb_trace_tsv|variant_calls_vcf>
    --output-folder <output_folder>
    [--variant-vcf-apply-filters <filter_value1,filter_value2,...>]
    [--variant-vcf-af-tag <FORMAT|INFO>/<tag>]
    [--population-variants-vcf <variants_vcf> | --population-markers-vcf <markers_vcf>]
    [--population-vcf-af-tag <FORMAT|INFO>/<tag>]
    [--population-snp-af-threshold <min_af>]

Example usage:
    # Example input datasets available in tests_data/contamination
    # DRAGEN's *.tmb.trace.tsv output
    plot-contamination-vafs \
        --variant-calls NA12878_Coriell_IX13680_F161339.tmb.trace.tsv \
        --output-folder contamination_vaf_plot

    # Variant calls VCF + population variants VCF
    plot-contamination-vafs \
        --variant-calls NA12878_Coriell_IX13680_F161339.hard-filtered.vcf \
        --variant-vcf-apply-filters 'PASS' \
        --variant-vcf-af-tag 'FORMAT/AF' \
        --population-variants-vcf population_variants.vcf \
        --population-vcf-af-tag 'INFO/AF' \
        --population-snp-af-threshold 0.01 \
        --output-folder contamination_vaf_plot

    # Variant calls VCF + population markers VCF
    plot-contamination-vafs \
        --variant-calls NA12878_Coriell_IX13680_F161339.hard-filtered.vcf \
        --variant-vcf-apply-filters 'PASS' \
        --variant-vcf-af-tag 'FORMAT/AF' \
        --population-markers-vcf population_markers.vcf \
        --output-folder contamination_vaf_plot
"""

import argparse
import logging
import re
import sys
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from clinical_tools.analysis.vcf import (
    BcftoolsIsecOutput,
    bgzip_and_index_vcf,
    collapse_multi_allelics,
    drop_genotypes,
    extract_biallelic_snps,
    filter_vcf,
    intersect_vcfs,
)
from clinical_tools.core.io import FileMode, open_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

# Exclude mitochondrial chromosome, ALT contigs, unplaced scaffolds, etc.
VALID_CHROMOSOMES = [str(i) for i in range(1, 23)] + ["X", "Y"]


def validate_vcf_af_tag(af_tag: str) -> str:
    """Validate that AF tag is properly formatted as <FORMAT|INFO>/<TAG>."""
    if not (af_tag.startswith("FORMAT/") or af_tag.startswith("INFO/")):
        raise argparse.ArgumentTypeError(
            f"Invalid tag '{af_tag}': must start with 'FORMAT/' or 'INFO/'"
        )
    return af_tag


def generate_population_markers_vcf(
    population_variants_vcf: Path, af_tag: str, af_threshold: float, output_folder: Path
) -> Path:
    """Subset population variants VCF to population markers VCF.

    Population markers are defined as bi-allelic SNPs with AF >= the specified
    threshold.

    Args:
        population_variants_vcf: Path to VCF of known population variants.
        af_tag: <FORMAT|INFO>/<TAG> in population variants VCF to extract AFs from.
        af_threshold: Minimum AF for SNPs in population variants VCF to be included
            as population markers.
        output_folder: Directory to write population markers VCF to.

    Returns:
        Path to population markers VCF.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        vcf_stem = population_variants_vcf.name.removesuffix(".vcf.gz").removesuffix(
            ".vcf"
        )

        # Ensure population variants VCF is properly formatted: sites only and
        # multi-allelic sites are collapsed for consistent filtering of bi-allelic SNPs
        sites_only_vcf_path = Path(tmpdir) / f"{vcf_stem}.sites_only.vcf.gz"
        drop_genotypes(population_variants_vcf, sites_only_vcf_path)
        collapsed_vcf_path = Path(tmpdir) / f"{vcf_stem}.collapsed.vcf.gz"
        collapse_multi_allelics(sites_only_vcf_path, collapsed_vcf_path)

        # Subset VCF to population markers: bi-allelic SNPs above the specified AF
        # threshold
        biallelic_snps_vcf_path = Path(tmpdir) / f"{vcf_stem}.biallelic_snps.vcf.gz"
        extract_biallelic_snps(collapsed_vcf_path, biallelic_snps_vcf_path)
        population_markers_vcf_path = (
            output_folder / f"{vcf_stem}.biallelic_snps.minAF{af_threshold}.vcf.gz"
        )
        filter_vcf(
            biallelic_snps_vcf_path,
            f"{af_tag} >= {af_threshold}",
            population_markers_vcf_path,
        )

    return population_markers_vcf_path


def extract_af(af_tag: str, vcf_record_fields: list[str]) -> float:
    """Extract AF from specified column and tag.

    Args:
        af_tag: Column and tag to extract AF from, formatted as '<FORMAT|INFO>/<TAG>'.
        vcf_record_fields: List of fields from a single VCF record.

    Returns:
        AF as a float.
    """
    vcf_column, tag = af_tag.split("/")
    if vcf_column == "INFO":
        af_match = re.search(rf"(?:^|;){re.escape(tag)}=([^;]+)", vcf_record_fields[7])
        if af_match:
            return float(af_match.group(1))
        else:
            logging.error(
                f"'{af_tag}' not found in INFO field: {vcf_record_fields[7]}."
            )
            sys.exit(1)
    else:  # vcf_column == "FORMAT"
        format_fields_keys = vcf_record_fields[8].split(":")
        format_fields_values = vcf_record_fields[9].split(":")
        if tag in format_fields_keys:
            return float(format_fields_values[format_fields_keys.index(tag)])
        else:
            logging.error(f"'{tag}' not found in FORMAT field: {vcf_record_fields[8]}.")
            sys.exit(1)


def prepare_plot_data(
    variant_calls_path: Path,
    variant_calls_af_tag: str,
    filter_on_dragen_germline_status: bool,
) -> pd.DataFrame:
    """Convert variant calls to dataframe for downstream plotting.

    Variants are optionally filtered to DRAGEN-identified germline variants.

    Args:
        variant_calls_path: Path to variant calls.
        variant_calls_af_tag: Only applicable for variant calls in VCF format. Column
            and tag to extract VAFs from.
        filter_on_dragen_germline_status: If True, subset variant calls to
            DRAGEN-identified germline variants.

    Returns:
        Dataframe of germline variants with columns chrom, pos, ref, alt, vaf.
    """
    all_germline_variant_calls = []
    is_tmb_trace = str(variant_calls_path).endswith(".tmb.trace.tsv")
    with open_file(variant_calls_path, FileMode.READ) as variant_calls_file:
        for line in variant_calls_file:
            if line.startswith("#") or line.startswith("Chromosome"):
                continue
            if filter_on_dragen_germline_status and (
                "Germline_DB" not in line and "Germline_Proxi" not in line
            ):
                continue

            # Parse fields depending on input type
            fields = line.strip().split("\t")
            if is_tmb_trace:
                chrom, pos, ref, alt = fields[:4]
                vaf = float(fields[4])
            else:
                chrom, pos, ref, alt = fields[0], fields[1], fields[3], fields[4]
                vaf = extract_af(variant_calls_af_tag, fields)

            all_germline_variant_calls.append(
                {"chrom": chrom, "pos": pos, "ref": ref, "alt": alt, "vaf": vaf}
            )

    return pd.DataFrame(all_germline_variant_calls)


def plot_contamination_vafs(
    germline_variant_calls_df: pd.DataFrame, output_folder: Path
) -> None:
    """Plot VAFs of germline SNVs/variants.

    Args:
        germline_variant_calls_df: Dataframe of germline variants with columns chrom,
            pos, ref, alt, vaf.
        output_folder: Directory to write the VAF plot and corresponding data to.
    """
    # Filter for valid chromosomes (autosomal + sex chromosomes), then sort by chrom
    # and pos
    germline_variant_calls_df["chrom_no_prefix"] = germline_variant_calls_df[
        "chrom"
    ].str.replace("chr", "")
    plot_data_df = germline_variant_calls_df[
        germline_variant_calls_df["chrom_no_prefix"].isin(VALID_CHROMOSOMES)
    ]
    plot_data_df["chrom_no_prefix"] = pd.Categorical(
        plot_data_df["chrom_no_prefix"], categories=VALID_CHROMOSOMES, ordered=True
    )
    plot_data_df.sort_values(["chrom_no_prefix", "pos"], inplace=True)

    # Plot VAFs
    num_germline_variants = len(plot_data_df)
    plot_data_df["x"] = range(num_germline_variants)
    fig, ax = plt.subplots(
        figsize=(min(max(8, num_germline_variants / 150), 30), 5)
    )  # scale width by number of variants
    ax.scatter(
        plot_data_df["x"],
        plot_data_df["vaf"],
        s=6,
        alpha=0.8,
        color="#015196",
        linewidths=0,
        zorder=2,
    )

    # Identify chromosome boundaries to add separator lines
    chrom_boundaries_df = plot_data_df.groupby("chrom_no_prefix", observed=True)[
        "x"
    ].agg(["min", "max"])
    x_labels = {}
    for chrom, row in chrom_boundaries_df.iterrows():
        if row["min"] > 0:
            # Subtract 0.5 to position line between points of adjacent chromosomes
            ax.axvline(row["min"] - 0.5, color="lightgrey", linewidth=0.8, zorder=1)
        label_pos = (row["min"] + row["max"]) / 2
        x_labels[label_pos] = str(chrom)

    ax.set_xlim(-0.5, num_germline_variants - 0.5)  # offset padding to center labels
    ax.set_xticks(list(x_labels.keys()))
    ax.set_xticklabels(x_labels.values())
    ax.tick_params(axis="x", length=0, labelsize=8)
    ax.set_xlabel("Chromosome", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="y", labelsize=8)
    ax.set_ylabel("Variant allele frequency (VAF)", fontsize=10)
    ax.axhline(0.5, color="#FDB339", linestyle="--", linewidth=1.5)
    ax.axhline(0.25, color="grey", linestyle="--", linewidth=1.0)
    ax.axhline(0.75, color="grey", linestyle="--", linewidth=1.0)
    fig.tight_layout()

    # Save plot and write data to output folder
    fig.savefig(output_folder / "contamination_vafs.png", dpi=300)
    plt.close(fig)
    plot_data_df[["chrom", "pos", "ref", "alt", "vaf"]].to_csv(
        output_folder / "contamination_vafs_plot_data.tsv", index=False
    )
    logging.info(f"Total germline variants plotted: {num_germline_variants}")


def main() -> None:
    """Plot VAFs of germline variants."""
    parser = argparse.ArgumentParser(
        description=(
            "Plot allele frequencies of germline variants to assess sample "
            "contamination."
        )
    )
    parser.add_argument(
        "-v",
        "--variant-calls",
        help=(
            "Path to variant calls file. Supported files include DRAGEN's "
            "*.tmb.trace.tsv and *.hard-filtered.vcf.gz, or a VCF from other variant "
            "callers."
        ),
        required=True,
    )
    parser.add_argument(
        "-pv",
        "--population-variants-vcf",
        help=(
            "Path to VCF of known population variants to identify common bi-allelic "
            "SNP markers from. Required if --population-markers-vcf is not provided "
            "and the supplied variants call file is not DRAGEN's *.tmb.trace.tsv or "
            "*.hard-filtered.vcf.gz."
        ),
    )
    parser.add_argument(
        "-pm",
        "--population-markers-vcf",
        help=(
            "Path to VCF of population marker sites. Required if "
            "--population-variants-vcf is not provided and the supplied variant calls "
            "file is not DRAGEN's *.tmb.trace.tsv or *.hard-filtered.vcf.gz."
        ),
    )
    parser.add_argument(
        "-vfilters",
        "--variant-vcf-apply-filters",
        help=(
            "Only applicable for VCF inputs. Comma-separated list of FILTER values to "
            "apply to the variant calls (default: 'PASS')."
        ),
        default="PASS",
    )
    parser.add_argument(
        "-vaf",
        "--variant-vcf-af-tag",
        help=(
            "Only applicable for VCF inputs. Column and tag in variant calls VCF to "
            "extract SNV allele frequencies from. Specified as follows: "
            "<FORMAT|INFO>/<TAG> (default: 'FORMAT/AF')."
        ),
        type=validate_vcf_af_tag,
        default="FORMAT/AF",
    )
    parser.add_argument(
        "-paf",
        "--population-vcf-af-tag",
        help=(
            "Column and tag in population markers VCF to extract SNP allele "
            "frequencies from. Specified as follows: <FORMAT|INFO>/<TAG> "
            "(default: 'INFO/AF')."
        ),
        type=validate_vcf_af_tag,
        default="INFO/AF",
    )
    parser.add_argument(
        "-paft",
        "--population-snp-af-threshold",
        help=(
            "Minimum allele frequency for SNPs in the population variants VCF to be "
            "included as markers (default: 0.01)."
        ),
        type=float,
        default=0.01,
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        help="Name of folder to output intermediate VCFs, VAF plot and plot data to.",
        required=True,
    )

    # Parse args
    args = parser.parse_args()
    variant_calls = Path(args.variant_calls)
    population_variants_vcf = (
        Path(args.population_variants_vcf) if args.population_variants_vcf else None
    )
    population_markers_vcf = (
        Path(args.population_markers_vcf) if args.population_markers_vcf else None
    )
    variant_vcf_apply_filters = args.variant_vcf_apply_filters
    variant_calls_af_tag = args.variant_vcf_af_tag
    population_vcf_af_tag = args.population_vcf_af_tag
    population_snp_af_threshold = args.population_snp_af_threshold
    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Validate args
    is_dragen_output = (
        str(variant_calls).endswith(".tmb.trace.tsv")
        or "hard-filtered.vcf" in variant_calls.name
    )
    if not is_dragen_output and not (population_variants_vcf or population_markers_vcf):
        logging.error(
            "--population-variants-vcf or --population-markers-vcf must be provided if "
            "the input VCF is not DRAGEN's *.tmb.trace.tsv or *.hard-filtered.vcf.gz."
        )
        sys.exit(1)
    if str(variant_calls).endswith(".tmb.trace.tsv"):
        variant_vcf_apply_filters = None  # no FILTER column in *.tmb.trace.tsv
        if population_variants_vcf or population_markers_vcf:
            logging.warning(
                "DRAGEN's *.tmb.trace.tsv passed as input. Ignoring supplied "
                "population variants/markers VCF."
            )
            population_variants_vcf, population_markers_vcf = None, None

    # Subset population variants to population markers (i.e. common bi-allelic SNPs)
    if population_variants_vcf and not population_markers_vcf:
        logging.info(
            f"Selecting population markers from population variants VCF - bi-allelic "
            f"SNPs with AF >= {population_snp_af_threshold}."
        )
        population_markers_vcf = generate_population_markers_vcf(
            bgzip_and_index_vcf(population_variants_vcf),
            population_vcf_af_tag,
            population_snp_af_threshold,
            output_folder,
        )

    # Filter variant calls VCF to specified FILTER values
    vcf_stem = variant_calls.name.removesuffix(".vcf.gz").removesuffix(".vcf")
    if variant_vcf_apply_filters:
        variant_calls_filter_expression = " || ".join(
            f'FILTER~"{filter_val.strip()}"'
            for filter_val in variant_vcf_apply_filters.split(",")
        )
        variant_calls_filtered = output_folder / f"{vcf_stem}.filtered.vcf.gz"
        filter_vcf(
            bgzip_and_index_vcf(variant_calls),
            variant_calls_filter_expression,
            variant_calls_filtered,
        )
    else:
        variant_calls_filtered = variant_calls

    # Prepare plot data
    if population_markers_vcf:
        logging.info(
            "Intersecting variant calls with population markers to identify germline "
            "SNVs for VAF plotting."
        )
        variant_calls_germline = intersect_vcfs(
            variant_calls_filtered,
            population_markers_vcf,
            BcftoolsIsecOutput.SHARED_FROM_VCF1,
            output_folder / f"{vcf_stem}.germline_snvs.vcf.gz",
        )

        logging.info("Preparing plot data from intersected germline SNVs.")
        germline_variant_calls_df = prepare_plot_data(
            variant_calls_germline,
            variant_calls_af_tag,
            filter_on_dragen_germline_status=False,
        )
        if germline_variant_calls_df.empty:
            logging.error(
                "No germline variants identified from intersect of variant calls and "
                "population markers, thus no data to plot."
            )
            sys.exit(1)
    else:
        logging.info("Preparing plot data from DRAGEN-identified germline variants.")
        germline_variant_calls_df = prepare_plot_data(
            variant_calls_filtered,
            variant_calls_af_tag,
            filter_on_dragen_germline_status=True,
        )

    # Plot
    plot_contamination_vafs(germline_variant_calls_df, output_folder)


if __name__ == "__main__":
    main()
