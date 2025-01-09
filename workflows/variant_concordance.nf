include {
    run_variant_concordance_engine
    summarize_variant_concordance
} from '../processes/variant_concordance'

// Function to build VCF pair channels
def build_vcf_pair_channels(truth_dir, query_dir) {
    return Channel
        .fromPath("${truth_dir}/*.{vcf,vcf.gz}")
        .map { truth_vcf ->
            def sampleName = truth_vcf.getName().replaceFirst(/\.vcf(\.gz)?$/, "")
            def query_vcf = file("${query_dir}/${sampleName}.vcf.gz") \
                ?: file("${query_dir}/${sampleName}.vcf")
            return tuple(sampleName, truth_vcf, query_vcf)
        }
}

workflow variant_concordance_workflow {
    main:
        // Create VCF pair channels
        vcf_pairs = build_vcf_pair_channels(params.truth_dir, params.query_dir)

        // Run variant concordance engine and summarize results
        vcf_pairs | run_variant_concordance_engine | summarize_variant_concordance
}
