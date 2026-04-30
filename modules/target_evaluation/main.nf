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
        vals[NR-1] = \$5
    } END {
        n = NR - 1

        if (n == 0) {
            print 1
            exit
        }

        asort(vals)

        if (n % 2 == 1) {
            median = vals[int((n+1)/2)]
        } else {
            median = (vals[n/2] + vals[n/2 + 1]) / 2
        }

        print tc / median

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

process GET_PER_BASE_STATS {
    label "dynamic_resource"
    tag "${sample_name}"

    // Current specs used here:
    // 1. Output all positions in bed file
    // 2. Min BQ and MQ of 0
    // 3. -A count anomalous reads pairs -x turn off overlaps removal (BQ 0 acceptable)
    // 4. -B to turn off BAQ recalculations based on reference genome
    // 5. Custom gawk to adjust for deletions & parse

    input:
    path targets_bed
    tuple val(sample_name), path(in_bam), val(pool_id)
    val min_bq_per_read
    val min_mq_per_read
    val output_percentile
    path cram_fasta

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: parsed_pileup

    script:
    OUT="${in_bam.baseName}.mpileup.per_base.parsed.txt"
    cram_extra_param = cram_fasta ? "--fasta-ref ${cram_fasta}" : " "
    """
    samtools mpileup -B -A -aa -x --min-BQ 0 --min-MQ 0 --output-MQ \
    --no-output-ends --no-output-ins --no-output-ins --no-output-del --no-output-del \
    ${cram_extra_param} --positions ${targets_bed} ${in_bam} |
    gawk -v OFS='\\t' '
    function decode_quality_score(target_chr, low, high, mid) {
        if (low > high) {return -10;}
        mid = int ((low+high)/2);
        if (sprintf("%c",mid) == target_chr) {
            return mid;
        } else if (sprintf("%c",mid) < target_chr) {
            return decode_quality_score(target_chr, mid + 1, high);
        } else {
            return decode_quality_score(target_chr, low, mid - 1);
        }
    }
    BEGIN {
        print "#CHROM","POS","COVERAGE","BASEQ_MED", \
        "BASEQ_Q1","MAPQ_MED","MAPQ_Q1","POOL";
    }
    {
        total_non_del=\$4; del_index = index(\$5, "*");
        while(del_index!=0) {
            total_non_del--;
            \$5=substr(\$5,1,del_index-1)substr(\$5,del_index+1);
            \$6=substr(\$6,1,del_index-1)substr(\$6,del_index+1);
            \$7=substr(\$7,1,del_index-1)substr(\$7,del_index+1);
            del_index = index(\$5, "*");
        }
        baseQ=0; mapQ=0; baseQs[1]=-1; mapQs[1]=-1; baseQ_count=0; mapQ_count=0; coverage=0;
        for(i=1;i<=total_non_del;i++) {
            baseChr=substr(\$6,i,1);
            mapChr=substr(\$7,i,1);
            baseQ=decode_quality_score(baseChr,0,255,127)-33;
            mapQ=decode_quality_score(mapChr,0,255,127)-33;
            if (baseQ >= ${min_bq_per_read.coverage_analysis} && mapQ >= ${min_mq_per_read.coverage_analysis}) {
                coverage++;
            }
            if (baseQ >= ${min_bq_per_read.baseq_analysis} && mapQ >= ${min_mq_per_read.baseq_analysis}) {
                baseQ_count++;
                baseQs[baseQ_count]=baseQ;
            }
            if (baseQ >= ${min_bq_per_read.mapq_analysis} && mapQ >= ${min_mq_per_read.mapq_analysis}) {
                mapQ_count++;
                mapQs[mapQ_count]=mapQ;
            }
        }
        asort(baseQs); asort(mapQs);
        p_index_baseq=int( ${output_percentile} * (baseQ_count-1) + 1.5 );
        p_index_mapq=int( ${output_percentile} * (mapQ_count-1) + 1.5 );
        if (baseQ_count==0) {p_index_baseq=1}
        if (mapQ_count==0) {p_index_mapq=1}
        print(\$1,\$2,coverage,baseQs[p_index_baseq],mapQs[p_index_mapq],"${pool_id}")
        delete baseQs; delete mapQs;
    }' - > ${OUT}
    """
}

process GET_PER_BASE_STATS_NO_PARSE {
    label "dynamic_resource"
    tag "${sample_name}"
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}/raw_mpileups", mode: 'copy'

    input:
    path(targets_bed)
    tuple val(sample_name), path(in_bam), val(pool_id)
    path cram_fasta

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: raw_mpileup_out

    script:
    OUT="${in_bam.baseName}.mpileup.raw.txt"
    cram_extra_param = cram_fasta ? "--fasta-ref ${cram_fasta}" : " "
    """
    samtools mpileup -B -A -aa -x --min-BQ 0 --min-MQ 0 --output-MQ \
    --no-output-ends --no-output-ins --no-output-ins --no-output-del --no-output-del \
    ${cram_extra_param} --positions ${targets_bed} ${in_bam} > ${OUT}
    """
}

process ADD_TARGET_LABELS {
    tag "${sample_name}"

    input:
    tuple val(sample_name), path(parsed_pileup), val(pool_id)
    path(targets_bed)
    val(metrics_thresholds_and_headings)

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
        print "#CHROM","POS","TRACT","POOL",
        "${metrics_thresholds_and_headings.cov.library_header}",
        "${metrics_thresholds_and_headings.bq.library_header}",
        "${metrics_thresholds_and_headings.mq.library_header}";
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
    val(target_fail_tolerance)
    val(metrics_thresholds_and_headings)

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
            "${metrics_thresholds_and_headings.cov.target_header}",
            "${metrics_thresholds_and_headings.bq.target_header}",
            "${metrics_thresholds_and_headings.mq.target_header}",
            "LEN","NUM_BASES_FAIL","PCT_BASES_FAIL";
    }
    {
        n=split(\$4, coverages, ","); split(\$5, baseQ1s, ","); split(\$6, mapQ1s, ",");
        bases_failed = gsub(/FAIL/, "", \$7);
        asort(coverages); asort(baseQ1s); asort(mapQ1s);
        p=int( ${target_fail_tolerance} * (n-1) + 1.5 );
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
    val(agg_percentile)
    val(metrics_thresholds_and_headings)

    output:
    tuple val("All_Samples"), path(OUT), val("All_Pools"), emit: all_libraries_per_base

    script:
    OUT="cohort_base_analysis.tsv"
    """
    grep -v '^#' ${combined_labelled_pileups} |
    sort -k1,1 -k2,2 -k3,3 |
    bedtools groupby -g 1,2,3 -c 5,6,7 -o collapse |
    awk -v OFS='\\t' '
    BEGIN {
        OFMT = "%.${params.decimals}f"
        print "#CHROM","POS","TRACT","POOL",
            "${metrics_thresholds_and_headings.cov.base_header}",
            "${metrics_thresholds_and_headings.bq.base_header}",
            "${metrics_thresholds_and_headings.mq.base_header}",
            "NUM_LIB_FAIL(COV)","NUM_LIB_FAIL(BQ)","NUM_LIB_FAIL(MQ)",
            "${metrics_thresholds_and_headings.cov.base_score_header}",
            "${metrics_thresholds_and_headings.bq.base_score_header}",
            "${metrics_thresholds_and_headings.mq.base_score_header}";
    }
    {
        n=split(\$4, coverages, ","); split(\$5, baseQ1s, ","); split(\$6, mapQ1s, ",");

        asort(coverages); asort(baseQ1s); asort(mapQ1s);
        p=int( ${agg_percentile} * (n-1) + 1.5 );

        lib_fail_cov=0; lib_fail_bq=0; lib_fail_mq=0;
        for (i = 1; i <= n; i++){
            if (coverages[i] < ${metrics_thresholds_and_headings.cov.threshold}) lib_fail_cov++;
            if (baseQ1s[i] < ${metrics_thresholds_and_headings.bq.threshold}) lib_fail_bq++;
            if (mapQ1s[i] < ${metrics_thresholds_and_headings.mq.threshold}) lib_fail_mq++;
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
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}/library_level", mode: 'copy'

    input:
    tuple val(sample_name), path(pre_scored_file), val(pool_id)
    val(metrics_thresholds_and_headings)

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
        if (\$5>=${metrics_thresholds_and_headings.cov.threshold} && \$6>=${metrics_thresholds_and_headings.bq.threshold} && \$7>=${metrics_thresholds_and_headings.mq.threshold}) {
            print \$0,"PASS";
        } else {
            print \$0,"FAIL";
        }
    }' ${pre_scored_file} > ${OUT}
    """
}

process SCORE_OUTPUT_ON_FIELD {
    tag "${sample_name}"
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}/${sample_name=='All_Samples' ? '' : 'library_level'}", mode: 'copy'

    input:
    tuple val(sample_name), path(pre_scored_file), val(pool_id)
    val(col_to_score)
    val(output_col_name)
    val(scoring_threshold)

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: scored_output

    script:
    OUT="${pre_scored_file.baseName.replaceFirst( "\\.scored",'')}.scored.txt"
    """
    awk -v OFS='\\t' '
    /^#/ {
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
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}/tracts", mode: 'copy'

    input:
    tuple val(sample_name), path(scored_file), val(pool_id)
    each(headers_dict)
    val(gap_tolerance)

    output:
    path(OUT), emit: tract_bed

    script:
    OUT="tracts.${headers_dict.base_score_output_header.toLowerCase()}.bed"
    //TODO: also target/all library file
    """
    awk -v OFS='\\t' '
    /^#/ {
        for (i=1; i<=NF; i++) col[\$i] = i
    }
    \$col["${headers_dict.base_score_output_header}"] ~ /FAIL/ {
        # Convert to bed format
        print \$1,\$2-1,\$2,\$3,\$col["${headers_dict.base_header}"]
    }' ${scored_file} |
    sort -k1,1 -k2,2n |
    bedtools merge -d ${gap_tolerance} -c 4,5 -o distinct,mean |
    awk -v OFS='\\t' '
    BEGIN {
        print "#chrom", "start", "end", "name", "mean_fail_centile_score"
    }
    {
        \$5 = sprintf("%.${params.decimals}f", \$5)
        print
    }' > ${OUT}
    """
}

process UNIONIZE_TRACTS {
    tag "Unionizer"
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}/tracts", mode: 'copy'

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

process GENERATE_PER_LIBRARY_QC_REPORT {
    tag "All_Samples"
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}", mode: 'copy'

    input:
    // flatten the list of pairs into one directory
    path "files/*"

    output:
    path("cohort_qc_report.tsv"), emit: final_table

    script:
    OUT="cohort_qc_report.tsv"
    """
    echo -e "SAMPLE_ID\t%_Bases_Failed\t%_Targets_Failed\tAvg_%_Bases_Failed_Per_Target" > ${OUT}

    for BASE_FILE in files/*.mpileup.per_base.parsed.labelled.scored.txt; do
        [ -e "\${BASE_FILE}" ] || continue

        FILENAME=\$(basename "\${BASE_FILE}")
        ID=\${FILENAME%%.mpileup*}

        AGGR_FILE="files/\${ID}.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt"

        if [[ -f "\${AGGR_FILE}" ]]; then
            # Metric calculation
            # %_Bases_Failed --> from library-level <LIB>.mpileup.per_base.parsed.labelled.scored.txt based on SCORE column (8)
            # %_Targets_Failed --> from library-level <LIB>.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt based on SCORE column (11)
            # Avg_%_Bases_Failed_Per_Target --> from library-level <LIB>.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt based on PCT_BASES_FAIL column (10) averaged for each file(library)

            BASE_STATS=\$(awk -F'\t' 'NR>1 {all++; if(\$8=="FAIL") fail++} END {if(all>0) printf "%.2f%%", (fail/all)*100; else print "0.00%"}' "\${BASE_FILE}")
            AGGR_STATS=\$(awk -F'\t' 'NR>1 {all++; if(\$11=="FAIL") fail++; sum+=\$10} END {if(all>0) printf "%.2f%%\t%.2f%%", (fail/all)*100, sum/all; else print "0.00%\t0.00%"}' "\${AGGR_FILE}")

            echo -e "\${ID}\t\${BASE_STATS}\t\${AGGR_STATS}" >> ${OUT}
        fi
    done
    """
}

process GENERATE_VISUALIZATION {
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}/plots", mode: 'copy'

    input:
    path(input_files)
    val(pool_ids)
    val(prefix)
    val(metrics_thresholds_and_headings)

    output:
    path(OUT)

    script:
    OUT="${prefix}_*"
    """
    plot-target-tracts \
    --input-files ${input_files} \
    --pool-ids ${pool_ids.join(' ')} \
    --prefix ${prefix} \
    --metrics-thresholds-and-headings '${groovy.json.JsonOutput.toJson(metrics_thresholds_and_headings)}'
    """
}

process GENERATE_COMMON_REGIONS_FAIL {
    tag "${sample_name}"
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}", mode: 'copy'

    input:
    tuple val(sample_name), path(all_libraries_per_base), val(pool)

    output:
    path(OUT), emit: common_fail_regions

    script:
    OUT="common_fail_regions.bed"
    """
    awk -v OFS="\\t" '
        \$11 > ${params.cohort_percent_library_fail_threshold * 100} ||
        \$12 > ${params.cohort_percent_library_fail_threshold * 100} ||
        \$13 > ${params.cohort_percent_library_fail_threshold * 100} {
            print \$1,\$2,\$2+1,\$3
        }
        ' ${all_libraries_per_base} |
        sort-bed - |
        bedtools merge -c 4 -o distinct \
        > ${OUT}
    """
}

process GENERATE_BOX_PLOTS {
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}/plots", mode: 'copy'

    input:
    tuple val(sample_name), path(input_file), val(threshold), val(separate_plots)

    output:
    path(OUT), emit: percent_failed_box_plot

    script:
    OUT = "failure_threshold_*.png"
    """
    plot-gene-boxplots \
    --input-file ${input_file} \
    --threshold ${threshold} \
    ${separate_plots.toBoolean() ? '--separate-plots' : ''}
    """
}
