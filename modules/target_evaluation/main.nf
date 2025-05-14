process build_per_base_bed {
    publishDir "${params.bams_dir}/target_eval_results"

    input:
        path bed_file
        val panel
    output:
        path "$OUT", emit: per_base_bed

    script:
    OUT="${publishDir}/${params.targets_bed}.per-base.bed"
    """
    build_per_base_bed ${params.targets_bed} $OUT
    """
}


//process get_baseq {}

process measure_per_base_depth {
    //container params.clinical_utils_container
    //tag "${meta.RGSM}.${variant_type}"
    //cpus 16
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

//process generate_metrics_tracts{}
