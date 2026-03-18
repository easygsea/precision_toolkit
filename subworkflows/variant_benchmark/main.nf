include {
    generate_fai
} from '../../modules/fasta/main'

include {
    run_happy as run_happy_raw
    run_happy as run_happy_curated
    run_sompy as run_sompy_raw
    run_sompy as run_sompy_curated
    run_truvari_bench as run_truvari_bench_curated
    run_truvari_bench as run_truvari_bench_raw
    run_truvari_refine as run_truvari_refine_curated
    run_truvari_refine as run_truvari_refine_raw
    run_wittyer as run_wittyer_raw
    run_wittyer as run_wittyer_curated
    summarize_diagnostic_metrics
} from '../../modules/variant_benchmark/main'

// Main variant benchmark workflow
workflow variant_benchmark_workflow {
    take:
        vcf_pairs
        vcf_tbi_pairs
        curated_vcf_pairs
        curated_vcf_tbi_pairs

    main:
        // Validate skip_raw parameter
        if (params.skip_raw && !params.spurious_variants_vcf) {
            error "skip_raw parameter can only be used when spurious_variants_vcf is provided"
        }

        // Initialize summary files collections
        def summary_files = []
        def summary_files_curated = []

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
                    "${params.variant_benchmark_subdir}/raw",
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
                    "${params.variant_benchmark_subdir}/curated",
                    "curated"
                ).happy_summary.collect()
            }
        } else if (params.variant_benchmark_engine == "sompy") {
            if (!params.genome_ref) error "genome_ref parameter is required for sompy engine"

            def genome_ref_path = file(params.genome_ref)

            // Check if .fai index file exists, if not generate it
            def genome_fai_path = file("${params.genome_ref}.fai")
            if (!genome_fai_path.exists()) {
                genome_fai_path = generate_fai(genome_ref_path).genome_fai
            }

            // Only run raw analysis if skip_raw is false
            if (!params.skip_raw) {
                summary_files = run_sompy_raw(
                    vcf_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.sompy_options,
                    "${params.variant_benchmark_subdir}/raw",
                    "raw"
                ).sompy_summary.collect()
            }

            // If spurious variants VCF is provided, run sompy on curated VCFs
            if (params.spurious_variants_vcf) {
                summary_files_curated = run_sompy_curated(
                    curated_vcf_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.sompy_options,
                    "${params.variant_benchmark_subdir}/curated",
                    "curated"
                ).sompy_summary.collect()
            }
        } else if (params.variant_benchmark_engine == "truvari") {
            if (!params.genome_ref) error "genome_ref parameter is required for truvari engine"

            def genome_ref_path = file(params.genome_ref)

            // Check if .fai index file exists, if not generate it
            def genome_fai_path = file("${params.genome_ref}.fai")
            if (!genome_fai_path.exists()) {
                genome_fai_path = generate_fai(genome_ref_path).genome_fai
            }

            def enable_refine = params.enable_refine
            if (params.enable_refine && params.truvari_bench_options.contains("--sizemax -1")) {
                log.warn " truvari refine is disabled when --sizemax=-1 to avoid performance issues with large SVs."
                enable_refine = false
            }

            // Only run raw analysis if skip_raw is false
            if (!params.skip_raw) {
                raw_results = run_truvari_bench_raw(
                    vcf_tbi_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.truvari_bench_options,
                    "${params.variant_benchmark_subdir}/raw",
                    "raw"
                )
                summary_files = raw_results.truvari_bench_summary
                    .concat(raw_results.truvari_parameters)
                    .collect()

                // If enable_refine is true, run truvari refine
                if (enable_refine) {
                    summary_files = run_truvari_refine_raw(
                        raw_results.truvari_output_dir,
                        genome_ref_path,
                        genome_fai_path,
                        params.truvari_refine_options,
                        "${params.variant_benchmark_subdir}/raw",
                        "raw"
                    ).truvari_refine_summary
                        .concat(raw_results.truvari_parameters)
                        .collect()
                }
            }

            // If spurious variants VCF is provided, run truvari on curated VCFs
            if (params.spurious_variants_vcf) {
                curated_results = run_truvari_bench_curated(
                    curated_vcf_tbi_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.truvari_bench_options,
                    "${params.variant_benchmark_subdir}/curated",
                    "curated"
                )
                summary_files_curated = curated_results.truvari_bench_summary
                    .concat(curated_results.truvari_parameters)
                    .collect()

                // If enable_refine is true, run truvari refine
                if (enable_refine) {
                    summary_files_curated = run_truvari_refine_curated(
                        curated_results.truvari_output_dir,
                        params.truvari_refine_options,
                        "${params.variant_benchmark_subdir}/curated",
                        "curated"
                    ).truvari_refine_summary
                        .concat(curated_results.truvari_parameters)
                        .collect()
                }
            }
        } else if (params.variant_benchmark_engine == "wittyer") {
            // Only run raw analysis if skip_raw is false
            if (!params.skip_raw) {
                summary_files = run_wittyer_raw(
                    vcf_pairs,
                    params.wittyer_options,
                    "${params.variant_benchmark_subdir}/raw",
                    "raw"
                ).wittyer_summary.collect()
            }

            // If spurious variants VCF is provided, run wittyer on curated VCFs
            if (params.spurious_variants_vcf) {
                summary_files_curated = run_wittyer_curated(
                    curated_vcf_pairs,
                    params.wittyer_options,
                    "${params.variant_benchmark_subdir}/curated",
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
            params.variant_benchmark_subdir,
            params.decimals,
            params.include_all_data_csv
        )
}
