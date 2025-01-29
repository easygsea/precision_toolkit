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

        // Create VCF pair channels
        vcf_pairs = build_vcf_pair_channels(params.truth_dir, params.query_dir)

        // Conditionally run processes based on the selected engine
        if (params.variant_concordance_engine == "happy") {
            // Validate genome_ref for happy
            if (!params.genome_ref) {
                error "genome_ref parameter is required for happy engine"
            }

            // Create genome reference channels
            genome_ref_channel = Channel.value(params.genome_ref)
            genome_fai_channel = genome_ref_channel.map { it + '.fai' }

            // Conditionally generate .fai index if it doesn't exist
            genome_fai_channel = genome_fai_channel.ifEmpty {
                generate_fai(genome_ref_channel).genome_fai
            }

            happy_results = run_happy(
                vcf_pairs, 
                genome_ref_channel, 
                genome_fai_channel, 
                params.happy_options,
                params.concordance_dir
            )
            summary_files = happy_results.happy_summary.collect()

            // If spurious_variants_vcf is provided, run the exclude_spurious_variants process
            if (params.spurious_variants_vcf) {
                // Run exclude_spurious_variants process for each sample
                curated_vcfs = exclude_spurious_variants(
                    vcf_pairs.map { sampleName, truth_vcf, query_vcf -> tuple(sampleName, query_vcf) },
                    params.spurious_variants_vcf
                )
            
                // Pair the curated VCFs with their corresponding truth VCFs
                curated_vcf_pairs = vcf_pairs
                    .combine(curated_vcfs)
                    .map { sampleName, truth_vcf, query_vcf, curated_vcf -> 
                        tuple(sampleName, truth_vcf, curated_vcf) 
                    }
            
                // Run happy analysis on the curated VCFs
                curated_happy_results = run_happy(
                    curated_vcf_pairs,
                    genome_ref_channel,
                    genome_fai_channel,
                    params.happy_options,
                    "${params.concordance_dir}/curated"
                )
            
                // Collect hap.py results after excluding spurious variants
                summary_files_curated = curated_happy_results.happy_summary.collect()
            }
        } else if (params.variant_concordance_engine == "wittyer") {
            wittyer_results = run_wittyer(
                vcf_pairs, 
                params.wittyer_options,
                params.concordance_dir
            )
            summary_files = wittyer_results.wittyer_summary
                // Prefix output with sampleName due to conflicting Wittyer.Stats.json links
                .map { stats_file ->
                    // Extract sample name
                    def taskDir = stats_file.getParent()
                    def sampleName = taskDir.getBaseName()

                    // Create new file name with sample
                    def newName = "${sampleName}.Wittyer.Stats.json"
                    def newFile = file("${taskDir}/${newName}")

                    // Rename and return
                    stats_file.renameTo(newFile)
                    return newFile
                }
                .collect()
        }

        // Process variant concordance results based on whether curated files exist
        if (params.spurious_variants_vcf) {
            // When spurious variants VCF is provided, process both raw and curated results
            summarize_variant_concordance(
                summary_files,         // raw files
                summary_files_curated, // curated files
                params.concordance_dir
            )
        } else {
            // When no spurious variants VCF, process only raw results
            summarize_variant_concordance(
                summary_files,  // raw files
                null,           // no curated files
                params.concordance_dir
            )
        }

    emit:
        summary_files
}
