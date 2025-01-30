include {
    generate_fai
    bgzip_vcf
    index_vcf
    exclude_spurious_variants as exclude_spurious_variants_truth
    exclude_spurious_variants as exclude_spurious_variants_query
    run_happy as run_happy_initial
    run_happy as run_happy_curated
    run_wittyer
    summarize_variant_concordance
} from '../processes/variant_concordance'

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

// Main variant concordance workflow
// Handles the complete variant concordance analysis pipeline
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

            def genome_ref_path = file(params.genome_ref)
            
            // Check if .fai index file exists, if not generate it
            // Using a simple file existence check is more straightforward than creating a channel
            def genome_fai_path = file("${params.genome_ref}.fai")
            if (!genome_fai_path.exists()) {
                genome_fai_path = generate_fai(genome_ref_path).genome_fai
            }

            // Run initial happy analysis
            happy_results = run_happy_initial(
                vcf_pairs, 
                genome_ref_path, 
                genome_fai_path, 
                params.happy_options,
                params.concordance_dir
            )
            summary_files = happy_results.happy_summary.collect()

            // If spurious_variants_vcf is provided, run the exclude_spurious_variants process
            if (params.spurious_variants_vcf) {
                def spurious_variants_vcf = file(params.spurious_variants_vcf)
                
                // Handle gzipped VCF
                def spurious_variants_vcf_gz = spurious_variants_vcf.toString().endsWith('.gz') ? 
                    spurious_variants_vcf : file("${params.spurious_variants_vcf}.gz")
                
                // Handle .tbi index
                def spurious_variants_vcf_tbi = file("${spurious_variants_vcf_gz}.tbi")
                def spurious_variants_vcf_tbi_exists = spurious_variants_vcf.toString().endsWith('.gz') ?
                    file("${params.spurious_variants_vcf}.tbi").exists() : spurious_variants_vcf_tbi.exists()

                // If input VCF is not gzipped and .gz file doesn't exist, generate it
                if (!spurious_variants_vcf.toString().endsWith('.gz') && !spurious_variants_vcf_gz.exists()) {
                    spurious_variants_vcf_gz = bgzip_vcf(spurious_variants_vcf).gzipped_vcf
                }

                // If .tbi index file doesn't exist, generate it
                if (!spurious_variants_vcf_tbi_exists) {
                    spurious_variants_vcf_tbi = index_vcf(spurious_variants_vcf_gz).indexed_vcf
                }

                // Create channels for truth and query VCFs
                truth_vcfs = vcf_pairs.map { sampleName, truth_vcf, query_vcf -> tuple(sampleName, truth_vcf) }
                query_vcfs = vcf_pairs.map { sampleName, truth_vcf, query_vcf -> tuple(sampleName, query_vcf) }

                // Run exclude_spurious_variants process for truth and query VCFs
                curated_truth = exclude_spurious_variants_truth(
                    truth_vcfs,
                    spurious_variants_vcf_gz,
                    spurious_variants_vcf_tbi,
                    "truth"
                ).curated_vcf
                curated_query = exclude_spurious_variants_query(
                    query_vcfs,
                    spurious_variants_vcf_gz,
                    spurious_variants_vcf_tbi,
                    "query"
                ).curated_vcf

                // Combine results while maintaining sample pairing
                curated_vcf_pairs = curated_truth.join(curated_query)
            
                // Run happy analysis on the curated VCFs
                curated_happy_results = run_happy_curated(
                    curated_vcf_pairs,
                    genome_ref_path,
                    genome_fai_path,
                    params.happy_options,
                    params.concordance_dir
                )
            
                // Collect hap.py results after excluding spurious variants
                summary_files_curated = curated_happy_results.happy_summary.collect()
            }
        } else if (params.variant_concordance_engine == "wittyer") {
            // Run wittyer analysis
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
