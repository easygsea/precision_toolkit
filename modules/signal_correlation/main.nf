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
    # Normalize VCFs to split multialleles
    bcftools norm -m- "${truth_vcf}" -o "${truth_vcf}.norm.vcf"
    bcftools norm -m- "${query_vcf}" -o "${query_vcf}.norm.vcf"

    # Extract signals from normalized VCFs
    mkdir -p "${truth_output_folder}"
    echo -e "CHROM\\tPOS\\tREF\\tALT\\t${truth_signal_name}" > "${truth_output}"
    bcftools query -f '%CHROM\\t%POS\\t%REF\\t%ALT\\t[%${truth_signal_name}]\\n' "${truth_vcf}.norm.vcf" >> "${truth_output}"

    mkdir -p "${query_output_folder}"
    echo -e "CHROM\\tPOS\\tREF\\tALT\\t${query_signal_name}" > "${query_output}"
    bcftools query -f '%CHROM\\t%POS\\t%REF\\t%ALT\\t[%${query_signal_name}]\\n' "${query_vcf}.norm.vcf" >> "${query_output}"
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
    val show_regression

    output:
    path("correlation_*.png"), emit: signal_correlation_plot
    path("correlation_*.tsv"), emit: signal_correlation_table

    script:
    def output_filename = "correlation_${truth_signal_name}_${query_signal_name}"
    def xlim_arg = xlim == "" ? "" : "--xlim ${xlim}"
    def ylim_arg = ylim == "" ? "" : "--ylim ${ylim}"
    def regression_arg = show_regression ? "--show-regression" : ""
    """
    export MPLCONFIGDIR=\$(mktemp -d)
    plot-signal-correlation \
    --truth-signal ${truth_signal_files} \
    --query-signal ${query_signal_files} \
    --output-filename ${output_filename} \
    ${xlim_arg} \
    ${ylim_arg} \
    ${regression_arg}
    """
}
