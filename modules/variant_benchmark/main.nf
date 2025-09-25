process run_happy {
    label "dynamic_resource"
    tag "${sample_name}"
    publishDir "${params.output_dir}/${output_dir ?: ''}/happy", mode: 'copy'

    input:
    tuple val(sample_name), path(truth_vcf), path(query_vcf)
    path genome_ref
    path genome_fai
    val happy_engine
    val happy_options
    val output_dir
    val label

    output:
    path("${sample_name}.${label}.summary.csv"), emit: happy_summary
    path("${sample_name}*"), emit: happy_outputs

    script:
    """
    export HGREF="${genome_ref}"
    mkdir -p scratch_happy

    /opt/hap.py/bin/hap.py \
    "${truth_vcf}" \
    "${query_vcf}" \
    -r "${genome_ref}" \
    -o "${sample_name}.${label}" \
    --engine=${happy_engine} \
    --scratch-prefix scratch_happy \
    ${happy_options}
    """
}

process run_sompy {
    label "dynamic_resource"
    tag "${sample_name}"
    publishDir "${params.output_dir}/${output_dir ?: ''}/sompy", mode: 'copy'

    input:
    tuple val(sample_name), path(truth_vcf), path(query_vcf)
    path genome_ref
    path genome_fai
    val sompy_options
    val output_dir
    val label

    output:
    path("*.stats.csv"), emit: sompy_summary
    path("${sample_name}*"), emit: sompy_outputs

    script:
    PREFIX = "${sample_name}.${label}"
    SCRATCH_DIR = "${PREFIX}.scratch_sompy"
    """
    export HGREF="${genome_ref}"

    /opt/hap.py/bin/som.py \
    ${truth_vcf} \
    ${query_vcf} \
    -r "${genome_ref}" \
    -o "${PREFIX}" \
    --scratch-prefix ${SCRATCH_DIR} \
    --keep-scratch \
    ${sompy_options}
    """
}

process run_wittyer {
    label "dynamic_resource"
    tag "${sample_name}"
    containerOptions = "-B /home"
    publishDir "${params.output_dir}/${output_dir ?: ''}/wittyer", mode: 'copy'

    input:
    tuple val(sample_name), path(truth_vcf), path(query_vcf)
    val wittyer_options
    val output_dir
    val label

    output:
    path("*/*Wittyer.Stats.json"), emit: wittyer_summary
    path("${sample_name}*"), emit: wittyer_outputs

    script:
    PREFIX = "${sample_name}.${label}"
    // CDI-90 workaround: clean witty.er invalid options
    def clean_options = wittyer_options.replaceAll('--evaluationMode=Default|--evaluationMode=d|--em=Default|--em=d', '')
    """
    witty.er -i "${query_vcf}" -t "${truth_vcf}" -o "${PREFIX}" ${clean_options}
    mv "${PREFIX}/Wittyer.Stats.json" "${PREFIX}/${PREFIX}.Wittyer.Stats.json"
    """
}

process summarize_diagnostic_metrics {
    publishDir "${params.output_dir}/${output_dir ?: ''}", mode: 'copy'

    input:
    val variant_benchmark_engine
    path raw_variant_benchmark_outputs
    path curated_variant_benchmark_outputs
    val diagnostic_metrics
    val concordance_tp
    val ci_method
    val ci_level
    val output_dir
    val decimals
    val include_all_data_csv

    output:
    path("${PREFIX}*"), emit: variant_benchmark_summary

    script:
    PREFIX = "diagnostic_metrics"
    """
    summarize-diagnostic-metrics --metrics ${diagnostic_metrics} \
        --engine "${variant_benchmark_engine}" \
        ${(raw_variant_benchmark_outputs != []) ? "--raw-files " + raw_variant_benchmark_outputs.collect().join(' ') : ""} \
        ${(curated_variant_benchmark_outputs != []) ? "--curated-files " + curated_variant_benchmark_outputs.collect().join(' ') : ""} \
        --tp-method "${concordance_tp}" \
        --ci-method "${ci_method}" \
        --ci-level ${ci_level} \
        --prefix "${PREFIX}" \
        --decimals ${decimals} \
        --include-all-data-csv "${include_all_data_csv}"
    """
}
