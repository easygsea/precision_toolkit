include {
    generate_fai
} from '../../modules/fasta/main'

include {
    bgzip_vcf
    index_vcf as index_spurious_variants_original_vcf
    index_vcf as index_spurious_variants_normalized_vcf
    normalize_vcf
} from '../../modules/vcf/main'

include {
    exclude_spurious_variants as exclude_spurious_variants_truth
    exclude_spurious_variants as exclude_spurious_variants_query
    run_happy as run_happy_raw
    run_happy as run_happy_curated
    run_wittyer as run_wittyer_raw
    run_wittyer as run_wittyer_curated
    summarize_variant_concordance
} from '../../modules/concordance/main'

// Function to build VCF pair channels
// This function creates a channel of tuples containing sample name, truth VCF, and query VCF
def build_vcf_pair_channels(truth_dir, query_dir) {
    return Channel
        .fromPath("${truth_dir}/*.{vcf,vcf.gz}")
        .map { truth_vcf ->
            def sampleName = truth_vcf.getName().replaceFirst(/\..*$/, "")
            def query_vcf = file("${query_dir}/${sampleName}.*.vcf.gz") ?:
                            file("${query_dir}/${sampleName}.*.vcf")
            return tuple(sampleName, truth_vcf, query_vcf)
        }
}

// Function to handle spurious variants processing
def process_spurious_variants(vcf_pairs, spurious_variants_vcf_path, collapse) {
    def spurious_variants_vcf = file(spurious_variants_vcf_path)
    if (!spurious_variants_vcf.exists()) error "Input file not found, please check: ${spurious_variants_vcf}"

    // Check and compress spurious variants VCF
    def spurious_variants_vcf_gz = spurious_variants_vcf.toString().endsWith('.gz') ?
        spurious_variants_vcf : file("${spurious_variants_vcf}.gz")
    if (!spurious_variants_vcf_gz.exists()) {
        spurious_variants_vcf_gz = bgzip_vcf(file(spurious_variants_vcf)).gzipped_vcf
    }

    // Check and index spurious variants VCF
    def spurious_variants_vcf_tbi = file("${spurious_variants_vcf_gz}.tbi")
    if (!spurious_variants_vcf_tbi.exists()) {
        spurious_variants_vcf_tbi = index_spurious_variants_original_vcf(spurious_variants_vcf_gz).indexed_vcf
    }

    // Normalize spurious variants VCF
    def normalized_spurious_variants_vcf = normalize_vcf(spurious_variants_vcf_gz, spurious_variants_vcf_tbi).normalized_vcf

    // Index normalized spurious variants VCF
    def normalized_spurious_variants_vcf_tbi = index_spurious_variants_normalized_vcf(normalized_spurious_variants_vcf).indexed_vcf

    def truth_vcfs = vcf_pairs.map { sampleName, truth_vcf, query_vcf -> tuple(sampleName, truth_vcf) }
    def query_vcfs = vcf_pairs.map { sampleName, truth_vcf, query_vcf -> tuple(sampleName, query_vcf) }

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

// Function to run happy analysis
def run_happy_analysis(vcf_pairs, genome_ref_path, genome_fai_path, happy_options, output_dir, label) {
    return label == "raw" ?
        run_happy_raw(
            vcf_pairs,
            genome_ref_path,
            genome_fai_path,
            happy_options,
            output_dir,
            label
        ).happy_summary.collect() :
        run_happy_curated(
            vcf_pairs,
            genome_ref_path,
            genome_fai_path,
            happy_options,
            output_dir,
            label
        ).happy_summary.collect()
}

// Function to run wittyer analysis
def run_wittyer_analysis(vcf_pairs, wittyer_options, output_dir, label) {
    return label == "raw" ?
        run_wittyer_raw(
            vcf_pairs,
            wittyer_options,
            output_dir,
            label
        ).wittyer_summary.collect() :
        run_wittyer_curated(
            vcf_pairs,
            wittyer_options,
            output_dir,
            label
        ).wittyer_summary.collect()
}

// Main variant concordance workflow
workflow variant_concordance_workflow {
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
        if (params.variant_concordance_engine == "happy") {
            if (!params.genome_ref) error "genome_ref parameter is required for happy engine"

            def genome_ref_path = file(params.genome_ref)

            // Check if .fai index file exists, if not generate it
            def genome_fai_path = file("${params.genome_ref}.fai")
            if (!genome_fai_path.exists()) {
                genome_fai_path = generate_fai(genome_ref_path).genome_fai
            }

            // Only run raw analysis if skip_raw is false
            if (!params.skip_raw) {
                summary_files = run_happy_analysis(
                    vcf_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.happy_options,
                    "${params.concordance_dir}/raw",
                    "raw"
                )
            }

            // If spurious variants VCF is provided, run happy on curated VCFs
            if (params.spurious_variants_vcf) {
                summary_files_curated = run_happy_analysis(
                    curated_vcf_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.happy_options,
                    "${params.concordance_dir}/curated",
                    "curated"
                )
            }
        } else if (params.variant_concordance_engine == "wittyer") {
            // Only run raw analysis if skip_raw is false
            if (!params.skip_raw) {
                summary_files = run_wittyer_analysis(
                    vcf_pairs,
                    params.wittyer_options,
                    "${params.concordance_dir}/raw",
                    "raw"
                )
            }

            // If spurious variants VCF is provided, run wittyer on curated VCFs
            if (params.spurious_variants_vcf) {
                summary_files_curated = run_wittyer_analysis(
                    curated_vcf_pairs,
                    params.wittyer_options,
                    "${params.concordance_dir}/curated",
                    "curated"
                )
            }
        }

        // Summarize variant concordance results
        summarize_variant_concordance(
            summary_files,
            summary_files_curated,
            params.concordance_dir
        )
}
