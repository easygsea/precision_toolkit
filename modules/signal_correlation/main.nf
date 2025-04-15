process extract_signal {
    label "dynamic_resource"
    tag "${sampleName}"
    publishDir "${params.output_dir}/signal_correlation", mode: 'copy'

    input:
    val truth_signal_name
    val query_signal_name
    tuple val(sampleName), path(truth_vcf), path(query_vcf)

    output:
    path("truth/${truth_signal_name}/*"), emit: truth_signal
    path("query/${query_signal_name}/*"), emit: query_signal

    script:
    def truth_output_folder = "truth/${truth_signal_name}"
    def query_output_folder = "query/${query_signal_name}"
    def truth_output = "${truth_output_folder}/${sampleName}_truth_${truth_signal_name}.tsv"
    def query_output = "${query_output_folder}/${sampleName}_query_${query_signal_name}.tsv"
    """
    # Extract signals from VCFs
    mkdir -p "${truth_output_folder}"
    echo -e "CHROM\\tPOS\\tREF\\tALT\\t${truth_signal_name}" > "${truth_output}"
    bcftools query -f '%CHROM\\t%POS\\t%REF\\t%ALT\\t[ %${truth_signal_name}]\\n' "${truth_vcf}" >> "${truth_output}"

    mkdir -p "${query_output_folder}"
    echo -e "CHROM\\tPOS\\tREF\\tALT\\t${query_signal_name}" > "${query_output}"
    bcftools query -f '%CHROM\\t%POS\\t%REF\\t%ALT\\t[ %${query_signal_name}]\\n' "${query_vcf}" >> "${query_output}"
    """
}

process plot_signal_correlation {
    label "dynamic_resource"
    publishDir "${params.output_dir}/signal_correlation", mode: 'copy'

    input:
    val truth_signal_name
    val query_signal_name
    path truth_signal_files
    path query_signal_files
    val xlim
    val ylim

    output:
    path("correlation_*.png"), emit: signal_correlation_plot

    script:
    def output_file = "correlation_${truth_signal_name}_${query_signal_name}.png"
    def xlim_arg = xlim == "" ? "" : "--xlim ${xlim}"
    def ylim_arg = ylim == "" ? "" : "--ylim ${ylim}"
    """
    plot-signal-correlation \
    --truth-signal ${truth_signal_files} \
    --query-signal ${query_signal_files} \
    --output ${output_file} \
    ${xlim_arg} \
    ${ylim_arg}
    """
}
