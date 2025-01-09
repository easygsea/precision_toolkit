process run_variant_concordance_engine {
    tag "${params.variant_concordance_engine} analysis"

    input:
    tuple val(sampleName), path(truth_vcf), path(query_vcf)

    output:
    path("${params.output_dir}/${params.variant_concordance_engine}/${sampleName}*"), emit: concordance_outputs

    script:
    if (params.variant_concordance_engine == "happy") {
        """
        export HGREF=${params.genome_ref}
        mkdir -p ${params.scratch_dir}
        mkdir -p ${params.output_dir}/${params.variant_concordance_engine}
        /opt/hap.py/bin/hap.py \
        ${truth_vcf} \
        ${query_vcf} \
        -r ${params.genome_ref} \
        -o ${params.output_dir}/${params.variant_concordance_engine}/${sampleName} \
        --engine=vcfeval \
        --scratch-prefix ${params.scratch_dir} \
        --write-vcf \
        --write-counts
        """
    }
}

process summarize_variant_concordance {
    tag "summarize variant concordance"

    input:
    path concordance_outputs

    output:
    file("output_clinical_tools/concordance_cnv.md")
    file("output_clinical_tools/concordance_cnv.docx")

    script:
    """
    compute-variant-concordance -t ${params.variant_concordance_engine} \
        -f ${concordance_outputs.collect().join(' ')} \
        --md-output output_clinical_tools/concordance_cnv.md \
        --docx-output output_clinical_tools/concordance_cnv.docx
    """
}
