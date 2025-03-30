process exclude_spurious_variants {
    tag "${sampleName}"

    input:
    tuple val(sampleName), path(original_vcf)
    path normalized_spurious_vcf
    path normalized_spurious_vcf_tbi
    val label
    val collapse // collapse option for bcftools isec

    output:
    tuple val(sampleName), path("${sampleName}.${label}.no_spurious.vcf.gz"), emit: no_spurious_vcf

    script:
    """
    # Check and compress original VCF if needed
    if [[ ${original_vcf} != *.gz ]]; then
        bgzip -c ${original_vcf} > ${original_vcf}.gz
        mv ${original_vcf}.gz ${original_vcf}
    fi

    # Index original VCF if needed
    if [[ ! -f ${original_vcf}.tbi ]]; then
        tabix -p vcf ${original_vcf}
    fi

    # Normalize and decompose multiallelic variants in original VCF
    bcftools norm -m -any ${original_vcf} -o normalized_original.vcf.gz

    # Index normalized original VCF
    tabix -p vcf normalized_original.vcf.gz

    # Perform variant exclusion using bcftools isec on normalized VCFs
    bcftools isec --collapse ${collapse} --complement --write 1 --output-type z \
        --output ${sampleName}.${label}.no_spurious.vcf.gz normalized_original.vcf.gz ${normalized_spurious_vcf}
    """
}

process run_happy {
    label "dynamic_resource"
    tag "${sampleName}"
    publishDir "${params.output_dir}/${output_dir ?: ''}/happy", mode: 'copy'

    input:
    tuple val(sampleName), path(truth_vcf), path(query_vcf)
    path genome_ref
    path genome_fai
    val happy_options
    val output_dir
    val label

    output:
    path("${sampleName}.${label}.summary.csv"), emit: happy_summary
    path("${sampleName}*"), emit: happy_outputs

    script:
    """
    export HGREF=${genome_ref}
    mkdir -p scratch_happy

    /opt/hap.py/bin/hap.py \
    ${truth_vcf} \
    ${query_vcf} \
    -r ${genome_ref} \
    -o ${sampleName}.${label} \
    --engine=vcfeval \
    --scratch-prefix scratch_happy \
    ${happy_options}
    """
}

process run_wittyer {
    label "dynamic_resource"
    tag "${sampleName}"
    containerOptions = "-B /home"
    publishDir "${params.output_dir}/${output_dir ?: ''}/wittyer", mode: 'copy'

    input:
    tuple val(sampleName), path(truth_vcf), path(query_vcf)
    val wittyer_options
    val output_dir
    val label

    output:
    path("*/*Wittyer.Stats.json"), emit: wittyer_summary
    path("${sampleName}*"), emit: wittyer_outputs

    script:
    PREFIX = "${sampleName}.${label}"
    """
    witty.er -i ${query_vcf} -t ${truth_vcf} -o ${PREFIX} ${wittyer_options}
    mv ${PREFIX}/Wittyer.Stats.json ${PREFIX}/${PREFIX}.Wittyer.Stats.json
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
    val output_dir

    output:
    path("${PREFIX}*"), emit: variant_benchmark_summary

    script:
    PREFIX = "diagnostic_metrics"
    """
    summarize-diagnostic-metrics --metrics ${diagnostic_metrics} \
        --engine ${variant_benchmark_engine} \
        ${(raw_variant_benchmark_outputs != []) ? "--raw-files " + raw_variant_benchmark_outputs.collect().join(' ') : ""} \
        ${(curated_variant_benchmark_outputs != []) ? "--curated-files " + curated_variant_benchmark_outputs.collect().join(' ') : ""} \
        --tp-method ${concordance_tp} \
        --prefix ${PREFIX}
    """
}
