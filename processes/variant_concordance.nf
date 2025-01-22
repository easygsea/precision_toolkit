process generate_fai {
    tag "${genome_ref}"

    publishDir "${params.output_dir}/indices", mode: 'copy'

    input:
    path genome_ref

    output:
    path "${genome_ref}.fai", emit: genome_fai

    script:
    """
    samtools faidx ${genome_ref}
    """
}

process run_happy {
    tag "${sampleName}"
    publishDir "${params.output_dir}/happy", mode: 'copy'

    input:
    tuple val(sampleName), path(truth_vcf), path(query_vcf)
    path genome_ref
    path genome_fai
    val happy_options

    output:
    path("${sampleName}.summary.csv"), emit: happy_summary
    path("${sampleName}*"), emit: happy_outputs

    script:
    """
    export HGREF=${genome_ref}
    mkdir -p scratch_happy

    /opt/hap.py/bin/hap.py \
    ${truth_vcf} \
    ${query_vcf} \
    -r ${genome_ref} \
    -o ${sampleName} \
    --engine=vcfeval \
    --scratch-prefix scratch_happy \
    ${happy_options}
    """
}

process run_wittyer {
    tag "${sampleName}"
    containerOptions = "-B /home"
    publishDir "${params.output_dir}/wittyer", mode: 'copy'

    input:
    tuple val(sampleName), path(truth_vcf), path(query_vcf)
    val wittyer_options

    output:
    path("*/*Wittyer.Stats.json"), emit: wittyer_summary
    path("${sampleName}*"), emit: wittyer_outputs

    script:
    """
    witty.er -i ${query_vcf} -t ${truth_vcf} -o ${sampleName} ${wittyer_options}
    """
}

process summarize_variant_concordance {
    tag "summarize variant concordance"
    publishDir "${params.output_dir}", mode: 'copy'

    input:
    path concordance_outputs

    output:
    path("${PREFIX}*"), emit: variant_concordance_summary

    script:
    PREFIX="variant_concordance"
    """
    summarize-variant-concordance --type ${params.variant_concordance_engine} \
        --files ${concordance_outputs.collect().join(' ')} \
        --prefix ${PREFIX}
    """
}