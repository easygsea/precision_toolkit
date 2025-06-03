process build_per_base_bed {
    publishDir "${params.bams_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed_path)
    val(targets_bed_name)

    output:
        path "$OUT", emit: per_base_bed

    script:
    OUT="${targets_bed_name}.per-base.bed"
    //cant find this script (check out we did it before in CDI-30 ticket)
    """
    build_per_base_bed ${targets_bed_path} > $OUT
    """
}

process index_bam_file {
    publishDir "${params.bams_dir}/target_eval_results", mode: 'copy'

    input:
    [val(bed_file_name), path(bed_file_path)]
    //path bam_file

    output:
    path bam_file.bai

    script:
    """
    samtools index ${bam_file}
    """

}

process measure_per_base_depth {
    container params.clinical_utils_container
    publishDir "${params.bams_dir}/target_eval_results", mode: 'copy'
    cpus 16
    //label "track_panel_process"
    //tag "${meta.RGSM}.${variant_type}"

    input:
        path(bam_file),
        path(bai_file),
        path(bed_file)

    output:
        path(OUT), emit: perbase_cov_bed

    script:
    OUT="${bam_file}.perbasecoverage.txt"
    """
    samtools depth --min-BQ 10 --min-MQ 1 -a -b ${bed_file} -@ ${task.cpus} ${bam_file} > $OUT
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
