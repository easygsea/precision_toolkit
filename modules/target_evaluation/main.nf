process add_target_labels {
    //publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)
    tuple path(parsed_pileup), val(pool_id)

    output:
    tuple path(OUT), val(pool_id), emit: labelled_pileup

    script:
    OUT="${parsed_pileup.baseName}.labelled.txt"
    // NOTE: back to 0-indexed

    """
    awk 'BEGIN{OFS="\\t"} NR > 1 {print \$1, \$2-1, \$2, \$0}' ${parsed_pileup} |
    bedtools intersect -a - -b ${targets_bed} -wa -wb |
    awk -v OFS='\\t' '
    /^#/ {
        print "#CHROM","POS","TRACT","POOL","COVERAGE",\
        "BASEQ_MED","BASEQ_Q1","MAPQ_MED","MAPQ_Q1";
        next;
    }
    {
        print \$4,\$5,\$15,\$11,\$6,\$7,\$8,\$9,\$10;
    }' > ${OUT}
    """
}

process get_per_target_aggregated_stats {
    //publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)
    tuple path(labelled_pileup), val(pool_id)

    output:
    tuple path(OUT), val(pool_id), emit: per_target_aggregated

    script:
    OUT="${labelled_pileup.baseName}.target_aggregated.txt"
    // Gets per-target stats (median of cov, q1 of baseq_q1, q1 of mapq_q1)
    // Example Output: chr1	NA	SDHB_NM_003000_EXON02	586	NA	40	NA	60	PASS
    // TODO: add headers
    // TODO: ignore chimeric reads?

    """
    bedtools groupby -i ${labelled_pileup} -g 1,3,4 -c 5,7,9 -o collapse |
    awk -v OFS='\\t' '
    BEGIN {
        print "#CHROM","POS","TRACT","POOL","COVERAGE_Q1",\
        "BASEQ_Q1_MED","BASEQ_Q1_Q1","MAPQ_Q1_MED","MAPQ_Q1_Q1";
    }
    {
        n=split(\$4, coverages, ","); split(\$5, baseQ1s, ","); split(\$6, mapQ1s, ",");
        asort(coverages); asort(baseQ1s); asort(mapQ1s);
        q1=int((n + 3) / 4);
        print(\$1,"NA",\$2,\$3,coverages[q1],"NA",baseQ1s[q1],"NA",mapQ1s[q1]);
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
    //TODO: add header
    """
    sort -k1,1 -k2,2 -k3,3 ${combined_labelled_pileups} |
    bedtools groupby -g 1,2,3,4 -c 5,6,7,8,9 -o median > ${OUT}
    """
}

process score_output {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    // Expected format: chr1	17371254	SDHB_NM_003000_EXON02   IX00000	570	63	52	60	60
    path(labelled_pileup)
    val(cov_threshold)
    val(bq_threshold)
    val(mq_threshold)

    output:
    path(OUT)

    script:
    OUT="${labelled_pileup.baseName}.scored.txt"
    """
    awk -v OFS='\\t' '
    /^#/ {
        print \$0,"SCORE";
        next;
    }
    {
        if (\$5>=${cov_threshold} && \$7>=${bq_threshold} && \$9>=${mq_threshold}) {
            print \$0,"PASS";
        }
        else {
            print \$0,"FAIL";
        }
    }' ${labelled_pileup} > ${OUT}
    """
}

process generate_visualization {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    // Expected format: chr1	17371254	SDHB_NM_003000_EXON02	570	63	52	60	60
    path(input_files)
    val(pool_ids)
    val(prefix)
    val(cov_threshold)
    val(bq_threshold)
    val(mq_threshold)

    output:
    path(OUT)

    script:
    OUT="${prefix}_*"
    """
    plot-target-tracts \
    --input-files ${input_files} \
    --pool-ids ${pool_ids.join(' ')} \
    --prefix ${prefix} \
    --coverage-threshold ${cov_threshold} \
    --baseq-threshold ${bq_threshold} \
    --mapq-threshold ${mq_threshold} \
    """
}


//process generate_metrics_tracts{}
