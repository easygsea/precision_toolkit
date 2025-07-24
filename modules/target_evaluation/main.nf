process add_target_labels {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)
    path(parsed_pileup)

    output:
    path(OUT), emit: labelled_pileup

    script:
    OUT="${parsed_pileup.baseName}.labelled.txt"

    """
    awk 'BEGIN{OFS="\t"} {print \$1, \$2-1, \$2, \$0}' ${parsed_pileup} | \
    bedtools intersect -a - -b ${targets_bed} -wa -wb | \
    cut -f4,5,14,6-10 > ${OUT}
    # Output format: chr1	17345374	SDHB_NM_003000_EXON08   506	63	63	60	60
    """
}

process get_per_target_aggregated_stats {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)
    path(labelled_pileup)

    output:
    path(OUT), emit: per_target_aggregated

    script:
    OUT="${labelled_pileup.baseName}.target_aggregated.txt"
    """
    #get per-target stats (median of cov, median of baseq_q1, median of mapq_q1)
    bedtools groupby -i ${labelled_pileup} -g 1,3 -c 4,5,6,7,8 -o median > ${OUT}
    # Output format: chr1	17345374	SDHB_NM_003000_EXON08   506	63	63	60	60
    """
    //ignore chimeric reads?
}

process generate_per_base_summary {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(combined_labelled_pileups)

    output:
    path(OUT), emit: all_libraries_per_base

    script:
    OUT="all_libraries_per_base_median.txt"
    """
    bedtools groupby -i ${combined_labelled_pileups} -g 1,2,3 -c 4,5,6,7,8 -o median > ${OUT}
    """
}

process score_output {
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
    awk -v OFS='\\t' '{
        if (\$4>=${cov_threshold} && \$6>=${bq_threshold} && \$8>=${mq_threshold}) {
            print \$0,"PASS"}
        else {
            print \$0,"FAIL"}
    }' ${labelled_pileup} > ${OUT}
    """

}




//process generate_summary_per_library {}
//process generate_metrics_tracts{}
