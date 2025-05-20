include {
    generate_fai
} from '../../modules/fasta/main'

include {
    run_happy as run_happy_raw
    run_happy as run_happy_curated
    run_wittyer as run_wittyer_raw
    run_wittyer as run_wittyer_curated
    summarize_diagnostic_metrics
} from '../../modules/variant_benchmark/main'

include {
    build_vcf_pair_channels
    process_spurious_variants
} from '../../modules/utils/main'

// Main variant benchmark workflow
workflow variant_benchmark_workflow {
    main:
        // Validate input directories
        if (!file(params.truth_dir).exists()) error "Truth directory not found: ${params.truth_dir}"
        if (!file(params.query_dir).exists()) error "Query directory not found: ${params.query_dir}"

        // Validate skip_raw parameter
        if (params.skip_raw && !params.spurious_variants_vcf) {
            error "skip_raw parameter can only be used when spurious_variants_vcf is provided"
        }

        // Create VCF pair channels
        def vcf_pairs = build_vcf_pair_channels(params.truth_dir, params.query_dir)

        // Initialize summary files collections
        def summary_files = []
        def summary_files_curated = []

        // Process spurious variants if provided
        if (params.spurious_variants_vcf) {
            curated_vcf_pairs = process_spurious_variants(
                vcf_pairs,
                params.spurious_variants_vcf,
                params.collapse
            )
        }

        // Run analysis based on selected engine
        if (params.variant_benchmark_engine == "happy") {
            if (!params.genome_ref) error "genome_ref parameter is required for happy engine"

            def genome_ref_path = file(params.genome_ref)

            // Check if .fai index file exists, if not generate it
            def genome_fai_path = file("${params.genome_ref}.fai")
            if (!genome_fai_path.exists()) {
                genome_fai_path = generate_fai(genome_ref_path).genome_fai
            }

            // Only run raw analysis if skip_raw is false
            if (!params.skip_raw) {
                summary_files = run_happy_raw(
                    vcf_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.happy_engine,
                    params.happy_options,
                    "${params.variant_benchmark_dir}/raw",
                    "raw"
                ).happy_summary.collect()
            }

            // If spurious variants VCF is provided, run happy on curated VCFs
            if (params.spurious_variants_vcf) {
                summary_files_curated = run_happy_curated(
                    curated_vcf_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.happy_engine,
                    params.happy_options,
                    "${params.variant_benchmark_dir}/curated",
                    "curated"
                ).happy_summary.collect()
            }
        } else if (params.variant_benchmark_engine == "wittyer") {
            // Only run raw analysis if skip_raw is false
            if (!params.skip_raw) {
                summary_files = run_wittyer_raw(
                    vcf_pairs,
                    params.wittyer_options,
                    "${params.variant_benchmark_dir}/raw",
                    "raw"
                ).wittyer_summary.collect()
            }

            // If spurious variants VCF is provided, run wittyer on curated VCFs
            if (params.spurious_variants_vcf) {
                summary_files_curated = run_wittyer_curated(
                    curated_vcf_pairs,
                    params.wittyer_options,
                    "${params.variant_benchmark_dir}/curated",
                    "curated"
                ).wittyer_summary.collect()
            }
        }

        summarize_diagnostic_metrics(
            params.variant_benchmark_engine,
            summary_files,
            summary_files_curated,
            params.diagnostic_metrics,
            params.concordance_tp,
            params.ci_method,
            params.ci_level,
            params.variant_benchmark_dir,
            params.decimals
        )
}
