include {
    build_vcf_pair_channels
    process_spurious_variants
} from '../../modules/utils'

include {
    bgzip_vcf
    index_vcf
} from '../../modules/vcf'

workflow prepare_variant_benchmark_inputs {

    main:
    // Validate input directories
    if (!file(params.truth_dir).exists()) {
        error("Truth directory not found: ${params.truth_dir}")
    }
    if (!file(params.query_dir).exists()) {
        error("Query directory not found: ${params.query_dir}")
    }

    // Create VCF pair channels
    vcf_pairs = build_vcf_pair_channels(params.truth_dir, params.query_dir)
    vcf_tbi_pairs = channel.empty()
    curated_vcf_pairs = channel.empty()
    curated_vcf_tbi_pairs = channel.empty()

    // Process spurious variants if provided
    if (params.spurious_variants_vcf) {
        curated_vcf_pairs = process_spurious_variants(
            vcf_pairs,
            params.spurious_variants_vcf,
            params.collapse,
        )
    }

    // If engine is truvari, ensure truth and query VCFs are bgzipped and indexed
    if (params.variant_benchmark_engine == 'truvari') {
        // Label VCFs to avoid aliasing bgzip_vcf and index_vcf processes
        all_vcf_pairs_labelled = vcf_pairs
            .flatMap { sample_name, truth_vcf, query_vcf ->
                [
                    tuple("${sample_name}.raw_truth", truth_vcf),
                    tuple("${sample_name}.raw_query", query_vcf)
                ]
            }
            .mix(
                curated_vcf_pairs.flatMap { sample_name, truth_vcf, query_vcf ->
                    [
                        tuple("${sample_name}.curated_truth", truth_vcf),
                        tuple("${sample_name}.curated_query", query_vcf)
                    ]
                }
            )

        // Identify which VCFs need bgzipping and indexing, then process accordingly
        all_vcf_pairs_branched = all_vcf_pairs_labelled.branch { vcf ->
            bgzipped_and_indexed: vcf[1].toString().endsWith('.gz') && file("${vcf[1]}.tbi").exists()
            bgzipped: vcf[1].toString().endsWith('.gz')
            uncompressed: true
        }
        bgzipped = bgzip_vcf(all_vcf_pairs_branched.uncompressed).gzipped_vcf

        all_bgzipped_vcfs = bgzipped.mix(
            all_vcf_pairs_branched.bgzipped_and_indexed,
            all_vcf_pairs_branched.bgzipped,
        )
        all_vcf_indices = all_vcf_pairs_branched.bgzipped_and_indexed
            .map { label, vcf -> tuple(label, file("${vcf}.tbi")) }
            .mix(index_vcf(bgzipped.mix(all_vcf_pairs_branched.bgzipped)).indexed_vcf)

        // Separate back into vcf_tbi_pairs and curated_vcf_tbi_pairs
        all_bgzipped_vcfs_and_indices_branched = all_bgzipped_vcfs
            .join(all_vcf_indices)
            .branch { vcf ->
                raw_truth: vcf[0].endsWith('raw_truth')
                raw_query: vcf[0].endsWith('raw_query')
                curated_truth: vcf[0].endsWith('curated_truth')
                curated_query: vcf[0].endsWith('curated_query')
            }

        vcf_tbi_pairs = all_bgzipped_vcfs_and_indices_branched.raw_truth
            .map { label, vcf, tbi -> tuple(label.replace('.raw_truth', ''), vcf, tbi) }
            .join(
                all_bgzipped_vcfs_and_indices_branched.raw_query
                    .map { label, vcf, tbi -> tuple(label.replace('.raw_query', ''), vcf, tbi) }
            )

        curated_vcf_tbi_pairs = all_bgzipped_vcfs_and_indices_branched.curated_truth
            .map { label, vcf, tbi -> tuple(label.replace('.curated_truth', ''), vcf, tbi) }
            .join(
                all_bgzipped_vcfs_and_indices_branched.curated_query
                    .map { label, vcf, tbi -> tuple(label.replace('.curated_query', ''), vcf, tbi) }
            )
    }

    emit:
    vcf_pairs
    vcf_tbi_pairs
    curated_vcf_pairs
    curated_vcf_tbi_pairs
}
