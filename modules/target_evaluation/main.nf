process NORMALIZE_TO_TARGET {
    tag "${sample_name}"

    input:
    path(targets_bed)
    tuple val(sample_name), path(parsed_pileup), val(pool_id)
    val(target_coverage)

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: normalized_pileup

    script:
    OUT="${parsed_pileup.baseName}.normalized.txt"
    """
    echo "Starting calculation for ${parsed_pileup}" #info
    norm_factor=\$(awk -v tc=${target_coverage} '
    BEGIN {
        OFS="\\t"
    } NR > 1 {
        total += \$5
    } END {
        print tc / total * (NR-1)
    }' ${parsed_pileup} )
    echo "TARGET COVERAGE = ${target_coverage}" #info
    echo "NORM_FACTOR=\${norm_factor}" #info
    awk -v norm_factor=\${norm_factor} '
    BEGIN{
        OFS="\\t"
    } NR == 1 {
        print;
        next;
    } {
        \$5 = int(\$5 * norm_factor + 0.5);
        print;
    }' ${parsed_pileup} > ${OUT}
    """
}

process ADD_TARGET_LABELS {
    tag "${sample_name}"

    input:
    path(targets_bed)
    tuple val(sample_name), path(parsed_pileup), val(pool_id)

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: labelled_pileup

    script:
    OUT="${parsed_pileup.baseName}.labelled.txt"
    // NOTE: back to 0-indexed
    """
    awk 'BEGIN{OFS="\\t"} NR > 1 {print \$1, \$2-1, \$2, \$0}' ${parsed_pileup} |
    bedtools intersect -a - -b ${targets_bed} -wa -wb |
    awk -v OFS='\\t' '
    BEGIN {
        print "#CHROM","POS","TRACT","POOL","COVERAGE","BASEQ_Q1","MAPQ_Q1";
    }
    {
        print \$4,\$5,\$13,\$9,\$6,\$7,\$8;
    }' > ${OUT}
    """
}

process GET_PER_TARGET_AGGREGATED_STATS {
    tag "${sample_name}"

    input:
    path(targets_bed)
    tuple val(sample_name), path(labelled_pileup), val(pool_id)

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: per_target_aggregated

    script:
    OUT="${labelled_pileup.baseName}.target_aggregated.txt"
    """
    sort -V -k1,1 -k3,3 -k2,2n ${labelled_pileup} |
    bedtools groupby -inheader -i - -g 1,3,4 -c 5,6,7 -o collapse |
    awk -v OFS='\\t' '
    BEGIN {
        print "#CHROM","POS","TRACT","POOL","COVERAGE_Q1","BASEQ_Q1_Q1","MAPQ_Q1_Q1";
    }
    {
        n=split(\$4, coverages, ","); split(\$5, baseQ1s, ","); split(\$6, mapQ1s, ",");
        asort(coverages); asort(baseQ1s); asort(mapQ1s);
        q1=int((n + 3) / 4);
        print(\$1,"NA",\$2,\$3,coverages[q1],baseQ1s[q1],mapQ1s[q1]);
        delete coverages; delete baseQ1s; delete mapQ1s;
    }' - > ${OUT}
    """
}

process GENERATE_PER_BASE_SUMMARY {
    tag "All_Samples"

    input:
    path(combined_labelled_pileups)

    output:
    tuple val("All_Samples"), path(OUT), val("All_Pools"), emit: all_libraries_per_base

    script:
    OUT="summary_per_base_median.txt"
    """
    grep -v '^#' |
    sort -k1,1 -k2,2 -k3,3 ${combined_labelled_pileups} |
    bedtools groupby -g 1,2,3 -c 5,6,7 -o median |
    awk -v OFS='\\t' '
    BEGIN {
        print "#CHROM","POS","TRACT","POOL","COVERAGE_MED","BASEQ_MED_Q1","MAPQ_MED_Q1";
    }
    {
        print \$1,\$2,\$3,"AGGREGATE",\$4,\$5,\$6,\$7;
    }' > ${OUT}
    """
}

process SCORE_OUTPUT {
    tag "${sample_name}"
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    tuple val(sample_name), path(pre_scored_file), val(pool_id)
    tuple val(cov_threshold), val(bq_threshold), val(mq_threshold)

    output:
    tuple val(sample_name), path(OUT), val(pool_id)

    script:
    OUT="${pre_scored_file.baseName}.scored.txt"
    """
    awk -v OFS='\\t' '
    /^#/ {
        print \$0,"SCORE";
        next;
    }
    {
        if (\$5>=${cov_threshold} && \$6>=${bq_threshold} && \$7>=${mq_threshold}) {
            print \$0,"PASS";
        }
        else {
            print \$0,"FAIL";
        }
    }' ${pre_scored_file} > ${OUT}
    """
}

process GENERATE_VISUALIZATION {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(input_files)
    val(pool_ids)
    val(prefix)
    tuple val(cov_threshold), val(bq_threshold), val(mq_threshold)

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

//TODO: process generate_metrics_tracts{}
