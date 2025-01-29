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
    label "dynamic_resource"
    tag "${sampleName}"
    publishDir "${params.output_dir}/${output_dir ?: ''}/happy", mode: 'copy'

    input:
    tuple val(sampleName), path(truth_vcf), path(query_vcf)
    path genome_ref
    path genome_fai
    val happy_options
    val output_dir

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
    label "dynamic_resource"
    tag "${sampleName}"
    containerOptions = "-B /home"
    publishDir "${params.output_dir}/${output_dir ?: ''}/wittyer", mode: 'copy'

    input:
    tuple val(sampleName), path(truth_vcf), path(query_vcf)
    val wittyer_options
    val output_dir

    output:
    path("*/*Wittyer.Stats.json"), emit: wittyer_summary
    path("${sampleName}*"), emit: wittyer_outputs

    script:
    """
    witty.er -i ${query_vcf} -t ${truth_vcf} -o ${sampleName} ${wittyer_options}
    """
}

process summarize_variant_concordance {
    publishDir "${params.output_dir}/${output_dir ?: ''}", mode: 'copy'

    input:
    path raw_files
    path curated_files, optional: true
    val output_dir

    output:
    path("${PREFIX}*"), emit: variant_concordance_summary

    script:
    PREFIX = curated_files ? "variant_concordance_combined" : "variant_concordance_raw"
    """
    summarize-variant-concordance --engine ${params.variant_concordance_engine} \
        --raw-files ${raw_files.collect().join(' ')} \
        ${curated_files ? "--curated-files " + curated_files.collect().join(' ') : ""} \
        --prefix ${PREFIX}
    """
}

process bgzip_vcf {
    tag "${sampleName}"
    
    input:
    tuple val(sampleName), path(original_vcf)
    
    output:
    path("${original_vcf}.gz"), emit: gzipped_vcf
    
    script:
    """
    bgzip -c ${original_vcf} > ${original_vcf}.gz
    """
}

process index_vcf {
    tag "${sampleName}"
    
    input:
    path gzipped_vcf
    
    output:
    path("${gzipped_vcf}.tbi"), emit: indexed_vcf
    
    script:
    """
    tabix -p vcf ${gzipped_vcf}
    """
}

process exclude_spurious_variants {
    tag "${sampleName}"
    
    input:
    tuple val(sampleName), path(original_vcf)
    path exclude_spurious_variants
    
    output:
    path("${sampleName}.curated.vcf.gz"), emit: curated_vcf
    
    script:
    """
    # Determine if we need to bgzip
    if [[ ${original_vcf} != *.gz ]]; then
        mv ${original_vcf} ${original_vcf}.unzipped
        original_vcf=${original_vcf}.unzipped
    fi
    
    # Determine if we need to index
    if [[ ! -f ${original_vcf}.tbi ]]; then
        mv ${original_vcf} ${original_vcf}.unindexed
        original_vcf=${original_vcf}.unindexed
    fi
    
    # Perform variant exclusion
    bcftools isec --collapse both --complement --write 1 --output-type z \
        --output ${sampleName}.curated.vcf.gz ${spurious_variants_vcf} ${original_vcf}
    """
    
    exec:
    // Handle bgzip if needed
    if (original_vcf.toString().endsWith('.unzipped')) {
        original_vcf = bgzip_vcf(sampleName, original_vcf).gzipped_vcf
    }
    
    // Handle indexing if needed
    if (original_vcf.toString().endsWith('.unindexed')) {
        original_vcf = index_vcf(original_vcf).indexed_vcf
    }
}
