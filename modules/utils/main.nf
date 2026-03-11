// Utility module for shared functions
include {
    bgzip_vcf
    index_vcf as index_spurious_variants_original_vcf
    index_vcf as index_spurious_variants_normalized_vcf
    exclude_spurious_variants as exclude_spurious_variants_truth
    exclude_spurious_variants as exclude_spurious_variants_query
    normalize_vcf
} from '../../modules/vcf/main'

/**
 * Builds channels for paired VCF files from truth and query directories.
 *
 * @param truth_dir   Directory containing truth VCF files.
 * @param query_dir   Directory containing query VCF files.
 * @return            Channel of tuples containing sample name, truth VCF, and query VCF.
 */
def build_vcf_pair_channels(truth_dir, query_dir) {
    return Channel
        .fromPath("${truth_dir}/*.{vcf,vcf.gz}")
        .map { truth_vcf ->
            def sample_name = truth_vcf.getName().replaceFirst(/\..*$/, "")
            def query_vcf = file("${query_dir}/${sample_name}.*.vcf.gz") ?:
                            file("${query_dir}/${sample_name}.*.vcf")
            return tuple(sample_name, truth_vcf, query_vcf[0])
        }
}


/**
 * Process spurious variants in VCF pairs.
 *
 * Processes spurious variants in VCF pairs by excluding them from the truth and query VCF files.
 * It also normalizes the spurious variants VCF and indexes the normalized VCF.
 *
 * @param vcf_pairs            Channel of tuples containing sample name, truth VCF, and query VCF.
 * @param spurious_variants_vcf_path Path to the spurious variants VCF file.
 * @param collapse             Collapse option for bcftools isec.
 * @return                     Channel of tuples containing sample name, truth VCF, and query VCF.
 */
def process_spurious_variants(vcf_pairs, spurious_variants_vcf_path, collapse) {
    def spurious_variants_vcf = file(spurious_variants_vcf_path)
    if (!spurious_variants_vcf.exists()) error "Input file not found, please check: ${spurious_variants_vcf}"

    // Check and compress spurious variants VCF
    def spurious_variants_vcf_gz = spurious_variants_vcf.toString().endsWith('.gz') ?
        spurious_variants_vcf : file("${spurious_variants_vcf}.gz")
    if (!spurious_variants_vcf_gz.exists()) {
        spurious_variants_vcf_gz = bgzip_vcf(
            tuple("spurious_variants", file(spurious_variants_vcf))
        ).gzipped_vcf.map { label, vcf -> vcf }
    }

    // Check and index spurious variants VCF
    def spurious_variants_vcf_tbi = file("${spurious_variants_vcf_gz}.tbi")
    if (!spurious_variants_vcf_tbi.exists()) {
        spurious_variants_vcf_tbi = index_spurious_variants_original_vcf(
            spurious_variants_vcf_gz.map { gzipped_vcf -> tuple("spurious_variants", gzipped_vcf) }
        ).indexed_vcf.map { label, tbi -> tbi}
    }

    // Normalize spurious variants VCF
    def normalized_spurious_variants_vcf = normalize_vcf(spurious_variants_vcf_gz, spurious_variants_vcf_tbi).normalized_vcf

    // Index normalized spurious variants VCF
    def normalized_spurious_variants_vcf_tbi = index_spurious_variants_normalized_vcf(
        normalized_spurious_variants_vcf.map { vcf -> tuple("spurious_variants_normalized", vcf) }
    ).indexed_vcf.map { label, tbi -> tbi}

    def truth_vcfs = vcf_pairs.map { sample_name, truth_vcf, query_vcf -> tuple(sample_name, truth_vcf) }
    def query_vcfs = vcf_pairs.map { sample_name, truth_vcf, query_vcf -> tuple(sample_name, query_vcf) }

    def no_spurious_truth = exclude_spurious_variants_truth(
        truth_vcfs,
        normalized_spurious_variants_vcf,
        normalized_spurious_variants_vcf_tbi,
        "truth",
        collapse
    ).no_spurious_vcf

    def no_spurious_query = exclude_spurious_variants_query(
        query_vcfs,
        normalized_spurious_variants_vcf,
        normalized_spurious_variants_vcf_tbi,
        "query",
        collapse
    ).no_spurious_vcf

    return no_spurious_truth.join(no_spurious_query)
}
