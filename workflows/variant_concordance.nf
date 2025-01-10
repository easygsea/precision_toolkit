include {
    run_variant_concordance_engine
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
        // Create VCF pair channels
        vcf_pairs = build_vcf_pair_channels(params.truth_dir, params.query_dir)

        // Create a value channel for genome reference and its index
        genome_ref_channel = Channel.value(params.genome_ref)
        genome_fai_channel = genome_ref_channel.map { it + '.fai' }

        // Run variant concordance engine per sample
        concordance_outputs = run_variant_concordance_engine(
            vcf_pairs, genome_ref_channel, genome_fai_channel)

        // Summarize variant concordance across samples
        summarize_variant_concordance(concordance_outputs)
}
