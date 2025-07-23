process get_per_target_stats {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)
    path(labelled_pileup)

    output:
    path(OUT), emit: per_target

    script:
    OUT="${labelled_pileup.baseName}.target_aggregated.txt"
    """
    #get per-target stats
    bedtools groupby -i ${labelled_pileup} -g 1,8 -c 3,4,6 -o median > ${OUT}
    """
    //ignore chimeric reads?
}

process filter_low_scoring_bases {

    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(labelled_pileup)
    val(cov_threshold)
    val(bq_threshold)
    val(mq_threshold)

    output:
    path(OUT), emit: scored

    script:
    OUT="${labelled_pileup.baseName}.scored.txt"
    """
    awk -v OFS='\\t' '{if (\$3>=${cov_threshold} && \$5>=${bq_threshold} && \$7>=${mq_threshold}) {print \$0,"PASS"} \
    else {print \$0,"FAIL"} }' ${labelled_pileup} > ${OUT}
    """

}


process aggregate_per_base_across_libraries {

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

//process generate_summary_per_library {}
//process generate_metrics_tracts{}
