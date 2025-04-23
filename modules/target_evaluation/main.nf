process subset_bam {
    tag "${sampleName}"

    input:
    tuple val(sampleName), path(original_vcf)
    path(bam_file)
    path(bed_file)

    output:
    tuple val(sampleName), path("${sampleName}.${label}.no_spurious.vcf.gz"), emit: target_subset_bam
    path(OUT), emit:

    script:
    OUT="${bam_file}.target_subset.bam"
    """
        bedtools intersect -wa -a ${bed_file} -b ${bam_file} > $OUT
    """
}

process get_mapq_from_bam {
    tag "${meta.RGSM}"
    publishDir "${meta.target_eval_directory}/per_base_metrics", mode: 'copy'

    script:
    OUT-"${meta.RGSM}.mapq"
    """
        samtools view -F 2048 ${bam_file} | cut -f1,5 > $OUT
    """
    //ignore chimeric reads
}

process get_baseq {

}

process measure_per_base_depth {
    container params.clinical_utils_container
    tag "${meta.RGSM}.${variant_type}"
    cpus 16
    publishDir "${meta.panel_output}/QC", mode: 'copy'
    label "track_panel_process"
    input:
        path(bam_file)
        path(bed_file)

    output:

    script:
    OUT="per_base_target_space_coverage.txt"
    """
        samtools depth --min-BQ 10 --min-MQ 1 -a -@ ${task.cpus} ${bam_file} > $OUT
    """
}

process score_coverage {

    input:
        path(bam_file)
        path(bed_file)

    output:

    script:
    OUT="per_base_target_space_coverage.txt"
    """
        samtools coverage --min-BQ 10 --min-MQ 1 -b ${bed_file} -@ ${task.cpus} ${bam_file} > $OUT
    """
}

process generate_metrics_tracts{}
