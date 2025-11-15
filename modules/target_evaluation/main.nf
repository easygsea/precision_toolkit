process NORMALIZE_COVERAGE_TO_TARGET {
    tag "${sample_name}"

    input:
    tuple val(sample_name), path(parsed_pileup), val(pool_id)
    path(targets_bed)
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
    echo "NORM_FACTOR = \${norm_factor}" #info
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
    tuple val(sample_name), path(parsed_pileup), val(pool_id)
    path(targets_bed)

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
    tuple val(sample_name), path(labelled_pileup), val(pool_id)
    path(targets_bed)
    val agg_percentile

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: per_target_aggregated

    script:
    OUT="${labelled_pileup.baseName}.target_aggregated.txt"
    """
    grep -v ^# ${labelled_pileup} |
    sort -V -k1,1 -k3,3 -k2,2n |
    bedtools groupby -g 1,3,4 -c 5,6,7,8 -o collapse |
    awk -v OFS='\\t' '
    BEGIN {
        OFMT = "%.${params.decimals}f"
        print "#CHROM","POS","TRACT","POOL",
            "CENTILE"int(${agg_percentile}*100)"(COV)",
            "CENTILE"int(${agg_percentile}*100)"(BQ_Q1)",
            "CENTILE"int(${agg_percentile}*100)"(MQ_Q1)",
            "LEN","NUM_BASES_FAIL","PCT_BASES_FAIL";
    }
    {
        n=split(\$4, coverages, ","); split(\$5, baseQ1s, ","); split(\$6, mapQ1s, ",");
        bases_failed = gsub(/FAIL/, "", \$7);
        asort(coverages); asort(baseQ1s); asort(mapQ1s);
        p=int( ${agg_percentile} * (n-1) + 1.5 );
        print \$1,"NA",\$2,\$3,
            coverages[p],baseQ1s[p],mapQ1s[p],
            n,bases_failed,bases_failed/n*100;
        delete coverages; delete baseQ1s; delete mapQ1s;
    }' - > ${OUT}
    """
}

process GENERATE_PER_BASE_SUMMARY {
    tag "All_Samples"

    input:
    path(combined_labelled_pileups)
    tuple val(cov_threshold), val(bq_threshold), val(mq_threshold)
    val(agg_percentile)

    output:
    tuple val("All_Samples"), path(OUT), val("All_Pools"), emit: all_libraries_per_base

    script:
    OUT="all_libraries_per_base.txt"
    """
    grep -v '^#' ${combined_labelled_pileups} |
    sort -k1,1 -k2,2 -k3,3 |
    bedtools groupby -g 1,2,3 -c 5,6,7 -o collapse |
    awk -v OFS='\\t' '
    BEGIN {
        OFMT = "%.${params.decimals}f"
        print "#CHROM","POS","TRACT","POOL",
            "CENTILE"int(${agg_percentile}*100)"(COV)",
            "CENTILE"int(${agg_percentile}*100)"(BQ_Q1)",
            "CENTILE"int(${agg_percentile}*100)"(MQ_Q1)",
            "NUM_LIB_FAIL(COV)","NUM_LIB_FAIL(BQ)","NUM_LIB_FAIL(MQ)",
            "PCT_LIB_FAIL(COV)","PCT_LIB_FAIL(BQ)","PCT_LIB_FAIL(MQ)";
    }
    {
        n=split(\$4, coverages, ","); split(\$5, baseQ1s, ","); split(\$6, mapQ1s, ",");

        asort(coverages); asort(baseQ1s); asort(mapQ1s);
        p=int( ${agg_percentile} * (n-1) + 1.5 );

        lib_fail_cov=0; lib_fail_bq=0; lib_fail_mq=0;
        for (i = 1; i <= n; i++){
            if (coverages[i] < ${cov_threshold}) lib_fail_cov++;
            if (baseQ1s[i] < ${bq_threshold}) lib_fail_bq++;
            if (mapQ1s[i] < ${mq_threshold}) lib_fail_mq++;
        }

        print \$1,\$2,\$3,"AGGREGATE",coverages[p],baseQ1s[p],mapQ1s[p],
            lib_fail_cov,lib_fail_bq,lib_fail_mq,
            lib_fail_cov/n*100,lib_fail_bq/n*100,lib_fail_mq/n*100;

        delete coverages; delete baseQ1s; delete mapQ1s;
    }' > ${OUT}
    """
}

process SCORE_OUTPUT_ON_METRICS {
    tag "${sample_name}"
    publishDir "${params.output_dir}/target_eval_results/library_level", mode: 'copy'

    input:
    tuple val(sample_name), path(pre_scored_file), val(pool_id)
    tuple val(cov_threshold), val(bq_threshold), val(mq_threshold)

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: scored_output

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
        } else {
            print \$0,"FAIL";
        }
    }' ${pre_scored_file} > ${OUT}
    """
}

process SCORE_OUTPUT_ON_FIELD {
    tag "${sample_name}"
    publishDir "${params.output_dir}/target_eval_results/${sample_name=='All_Samples' ? '' : 'library_level'}", mode: 'copy'

    input:
    tuple val(sample_name), path(pre_scored_file), val(pool_id)
    tuple val(output_col_name), val(col_to_score), val(scoring_threshold)

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: scored_output

    script:
    OUT="${pre_scored_file.baseName.replaceFirst( "\\.scored",'')}.scored.txt"
    """
    awk -v OFS='\\t' '
    /^#/ {
        # Handle headers
        for (i=1; i<=NF; i++) col[\$i] = i
        print \$0,"${output_col_name}";
        next;
    }
    {
        if ( \$col["${col_to_score}"] < ${scoring_threshold}*100 ) {
            print \$0,"PASS";
        } else {
            print \$0,"FAIL";
        }
    }' ${pre_scored_file} > temp.txt && mv temp.txt ${OUT}
    """
}

process GENERATE_TRACTS {
    tag "${sample_name}"
    publishDir "${params.output_dir}/target_eval_results/tracts", mode: 'copy'

    input:
    tuple val(sample_name), path(scored_file), val(pool_id)
    each(metric)
    val(gap_tolerance)
    val(centile)

    output:
    path(OUT), emit: tract_bed

    script:
    OUT="tracts.${metric.toLowerCase()}.bed"
    //TODO: also target/all library file
    """
    awk -v OFS='\\t' '
    /^#/ {
        # Handle headers
        for (i=1; i<=NF; i++) col[\$i] = i
        print "# chrom start end name mean_score"
        next
    }
    \$col["${metric}"] ~ /FAIL/ {
        # Match tag of values column to calc mean of failed centile
        col_tag="CENTILE" int(${centile}*100) \
            "(${metric.replaceFirst("_SCORE","")}" \
            (("${metric}"!="COV_SCORE") ? "_Q1)" : ")")
        # Convert to bed format
        print \$1,\$2,\$2+1,\$3,\$col[col_tag]
    }' ${scored_file} |
    bedtools merge -d ${gap_tolerance} -c 4,5 -o distinct,mean |
    awk -v OFS='\\t' '{ \$5 = sprintf("%.${params.decimals}f", \$5); print }' > ${OUT}
    """
}

process UNIONIZE_TRACTS {
    tag "${sample_name}"
    publishDir "${params.output_dir}/target_eval_results/tracts", mode: 'copy'

    input:
    path(all_tracts_bed)

    output:
    path(OUT), emit: tract_bed

    script:
    OUT="tracts.unionized.bed"
    """
    sort-bed ${all_tracts_bed} | bedtools merge -c 4 -o distinct > ${OUT}
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
