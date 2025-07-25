process add_target_labels {
    //publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)
    path(parsed_pileup)

    output:
    path(OUT), emit: labelled_pileup

    script:
    OUT="${parsed_pileup.baseName}.labelled.txt"
    // Example Output: chr1	17345374	SDHB_NM_003000_EXON08   506	63	63	60	60

    """
    awk 'BEGIN{OFS="\\t"} {print \$1, \$2-1, \$2, \$0}' ${parsed_pileup} | \
    bedtools intersect -a - -b ${targets_bed} -wa -wb | \
    awk 'BEGIN {OFS="\\t"} {print \$4,\$5,\$14,\$6,\$7,\$8,\$9,\$10}' > ${OUT}
    """
}

process get_per_target_aggregated_stats {
    //publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)
    path(labelled_pileup)

    output:
    path(OUT), emit: per_target_aggregated

    script:
    OUT="${labelled_pileup.baseName}.target_aggregated.txt"
    // Gets per-target stats (median of cov, q1 of baseq_q1, q1 of mapq_q1)
    // Example Output: chr1	NA	SDHB_NM_003000_EXON02	586	NA	40	NA	60	PASS
    // TODO: add headers
    // TODO: ignore chimeric reads?

    """
    bedtools groupby -i ${labelled_pileup} -g 1,3 -c 4,5,6,7,8 -o collapse |
    awk 'BEGIN {OFS="\\t"} {
        n = split(\$3, coverages, ","); split(\$5, baseQ1s, ","); split(\$7, mapQ1s, ",");
        asort(coverages); asort(baseQ1s); asort(mapQ1s);
        q1 = int((n + 3) / 4);
        print (\$1, "NA", \$2, coverages[q1], "NA", baseQ1s[q1], "NA", mapQ1s[q1]);
        delete coverages; delete baseQ1s; delete mapQ1s;
    }' - > ${OUT}
    """
}

process generate_per_base_summary {
    //publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(combined_labelled_pileups)

    output:
    path(OUT), emit: all_libraries_per_base

    script:
    OUT="summary_per_base_median.txt"
    // Generates median of all bases within the target group
    // Output Example: chr1	17371254	SDHB_NM_003000_EXON02	570	63	52	60	60
    //TODO: add header
    // per-base aggregate median of quartiles
    """
    sort -k1,1 -k2,2 -k3,3 ${combined_labelled_pileups} |
    bedtools groupby -g 1,2,3 -c 4,5,6,7,8 -o median > ${OUT}
    """
}

process score_output {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    // Expected format: chr1	17371254	SDHB_NM_003000_EXON02	570	63	52	60	60
    path(labelled_pileup)
    val(cov_threshold)
    val(bq_threshold)
    val(mq_threshold)

    output:
    path(OUT)

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
