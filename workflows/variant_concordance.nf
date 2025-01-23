include {
    run_happy
    run_wittyer
    summarize_variant_concordance
} from '../processes/variant_concordance'

// Function to build VCF pair channels
def build_vcf_pair_channels(truth_dir, query_dir) {
    return Channel
        .fromPath("${truth_dir}/*.{vcf,vcf.gz}")
        .map { truth_vcf ->
            def sampleName = truth_vcf.getName().replaceFirst(/\..*$/, "")
            def query_vcf = file("${query_dir}/${sampleName}.*.vcf.gz") ?:
                            file("${query_dir}/${sampleName}.*.vcf")
            
            // Add error handling for missing query VCFs
            if (!query_vcf.exists()) {
                error "No matching query VCF found for sample: ${sampleName}"
            }
            
            return tuple(sampleName, truth_vcf, query_vcf)
        }
}

workflow variant_concordance_workflow {
    main:
        // Validate input directories exist
        if (!file(params.truth_dir).exists()) {
            error "Truth directory not found: ${params.truth_dir}"
        }
        if (!file(params.query_dir).exists()) {
            error "Query directory not found: ${params.query_dir}"
        }
        
        // Validate output directory
        def output_dir = file(params.output_dir)
        if (output_dir.exists() && !params.force) {
            error "Output directory exists. Use --force to overwrite: ${params.output_dir}"
        }

        // Validate required inputs
        if (!params.genome_ref) {
            error "genome_ref parameter is required"
        }

        // Create VCF pair channels
        vcf_pairs = build_vcf_pair_channels(params.truth_dir, params.query_dir)

        // Create a value channel for genome reference and its index
        genome_ref_channel = Channel.value(params.genome_ref)
        genome_fai_channel = genome_ref_channel.map { it + '.fai' }

        // Conditionally generate .fai index if it doesn't exist
        genome_fai_channel = genome_fai_channel.ifEmpty {
            generate_fai(genome_ref_channel).genome_fai
        }

        // Conditionally run processes based on the selected engine
        if (params.variant_concordance_engine == "happy") {
            happy_results = run_happy(vcf_pairs, genome_ref_channel, genome_fai_channel, params.happy_options)
            summary_files = happy_results.happy_summary.collect()
        } else if (params.variant_concordance_engine == "wittyer") {
            wittyer_results = run_wittyer(vcf_pairs, params.wittyer_options)
            summary_files = wittyer_results.wittyer_summary.collect()
        }

        // Summarize variant concordance after all summary files are ready
        summarize_variant_concordance(summary_files)

    emit:
        summary_files
}