process get_per_base_stats {
    label "dynamic_resource"
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)
    path(in_bam)

    output:
    path(OUT), emit: parsed_bam

    script:
    OUT="${in_bam}.mpileup.parsed"
    """
    samtools mpileup -A -a -x --min-BQ 10 --min-MQ 1 --output-MQ --positions ${TARGET_BED} ${IN_BAM} | \
    gawk -v OFS='\t' 'function ord(c,i) { for(i=0;i<256;i++){if (sprintf("%c", i) == c) return i} return -1 } \
    { total_non_del=\$4; del_index = index(\$5, "*"); \
      while(del_index!=0) { \
        total_non_del--;  \
        \$5=substr(\$5,1,del_index-1)substr(\$5,del_index+1); \
        \$6=substr(\$6,1,del_index-1)substr(\$6,del_index+1); \
        \$7=substr(\$7,1,del_index-1)substr(\$7,del_index+1); \
        del_index = index(\$5, "*"); \
      }; \
      baseQ=0; mapQ=0; for(i=1;i<=\$4;i++) { \
      baseChr = substr(\$6, i, 1); baseQ+=ord(baseChr)-33; mapChr=substr(\$7,i,1); mapQ+=ord(mapChr)-33;}; \
      print(\$1,\$2,total_non_del,baseQ/total_non_del,mapQ/total_non_del) \
    }' - > $OUT
    """
}

process get_per_tract_stats {
    //tag "${sampleName}"
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path(targets_bed)

    output:
    path(OUT)

    script:
    TEMP="${parsed_bam}.labelled.per-base"
    OUT="${parsed_bam}.labelled.tract_aggregated"
    """
    #label per base
    awk 'BEGIN{OFS="\t"} {print \$1, \$2-1, \$2, \$0}' ${parsed_bam} | \
    bedtools intersect -a - -b  ${targets_bed} -wa -wb | \
    cut -f4-8,12 > $TEMP

    #get per-tract stats
    bedtools groupby -i ${TEMP} -g 1,6 -c 3,4,5 -o mean > $OUT
    """
    //ignore chimeric reads
}

process check_all_bases_outputted {

    input:
    path(targets_bed)
    path(in_bam)

    output:

    script:
    """
    total_bases=$(awk '{sum+=(\$3-\$2)} END {print sum}' ${TARGET_BED})
    parsed_bases=$(wc -l ${IN_BAM}.mpileup.parsed.labelled.per-base|cut -d" " -f1)
    if [ \$total_bases -eq \$parsed_bases ]; then
        echo "Assertion passed: all bases accounted for \${total_bases}=\${parsed_bases}"
    else
        echo "Assertion failed: total bases in target space (\${total_bases}) does not match total parsed bases(\${parsed_bases})"
    fi
    """
}
