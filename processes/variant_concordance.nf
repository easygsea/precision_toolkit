process run_variant_concordance_engine {
    tag "${params.variant_concordance_engine} analysis"

    input:
    tuple val(sampleName), path(truth_vcf), path(query_vcf)
    path genome_ref
    path genome_fai

    output:
    path("${params.output_dir}/${params.variant_concordance_engine}/${sampleName}*"), emit: concordance_outputs

    script:
    if (params.variant_concordance_engine == "happy") {
        """
        export HGREF=${genome_ref}
        mkdir -p ${params.output_dir}/${params.variant_concordance_engine}
        mkdir -p scratch_happy
        # Check if .fai index exists for the genome reference
        if [ ! -f ${genome_fai} ]; then
            echo "Index file not found. Generating .fai index for ${genome_ref}..."
            samtools faidx ${genome_ref}
        else
            echo ".fai index found for ${genome_ref}."
        fi
        /opt/hap.py/bin/hap.py \
        ${truth_vcf} \
        ${query_vcf} \
        -r ${genome_ref} \
        -o ${params.output_dir}/${params.variant_concordance_engine}/${sampleName} \
        --engine=vcfeval \
        --scratch-prefix scratch_happy \
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
