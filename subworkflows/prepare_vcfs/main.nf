include {
    bgzip_vcf
    index_vcf as index_spurious_variants_original_vcf
    index_vcf as index_spurious_variants_normalized_vcf
    exclude_spurious_variants as exclude_spurious_variants_truth
    exclude_spurious_variants as exclude_spurious_variants_query
    normalize_vcf
} from '../../modules/vcf'

workflow process_spurious_variants {
    take:
    vcf_pairs
    spurious_variants_vcf_path
    collapse

    main:
    def spurious_variants_vcf = file(spurious_variants_vcf_path)
    if (!spurious_variants_vcf.exists()) error "Input file not found, please check: ${spurious_variants_vcf}"

    def spurious_variants_vcf_gz_path = spurious_variants_vcf.toString().endsWith('.gz') ?
        spurious_variants_vcf : file("${spurious_variants_vcf}.gz")
    def spurious_variants_vcf_gz = Channel.value(spurious_variants_vcf_gz_path)
    if (!spurious_variants_vcf_gz_path.exists()) {
        spurious_variants_vcf_gz = bgzip_vcf(
            tuple("spurious_variants", file(spurious_variants_vcf))
        ).gzipped_vcf.map { _label, vcf -> vcf }.first()
    }

    def spurious_variants_vcf_tbi_path = file("${spurious_variants_vcf_gz_path}.tbi")
    def spurious_variants_vcf_tbi = Channel.value(spurious_variants_vcf_tbi_path)
    if (!spurious_variants_vcf_gz_path.exists() || !spurious_variants_vcf_tbi_path.exists()) {
        spurious_variants_vcf_tbi = index_spurious_variants_original_vcf(
            spurious_variants_vcf_gz.map { gzipped_vcf -> tuple("spurious_variants", gzipped_vcf) }
        ).indexed_vcf.map { _label, tbi -> tbi }.first()
    }

    def normalized_spurious_variants_vcf = normalize_vcf(spurious_variants_vcf_gz, spurious_variants_vcf_tbi).normalized_vcf.first()

    def normalized_spurious_variants_vcf_tbi = index_spurious_variants_normalized_vcf(
        normalized_spurious_variants_vcf.map { vcf -> tuple("spurious_variants_normalized", vcf) }
    ).indexed_vcf.map { _label, tbi -> tbi }.first()

    def truth_vcfs = vcf_pairs.map { sample_name, truth_vcf, _query_vcf -> tuple(sample_name, truth_vcf) }
    def query_vcfs = vcf_pairs.map { sample_name, _truth_vcf, query_vcf -> tuple(sample_name, query_vcf) }

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

    emit:
    curated_vcf_pairs = no_spurious_truth.join(no_spurious_query)
}
