process get_per_base_stats {
    label "dynamic_resource"

    // Current specs used here:
    // 1, output all positions in bed file
    // 2. Min BQ of 10 consider BQ in calculations (ref old)
    // 3. Min MQ of 1 (ref old)
    // 4. -A count anomalous reads pairs -x turn off overlaps removal
    // 5. custom gawk to adjust for deletions & parse

    input:
    path(targets_bed)
    path(in_bam)

    output:
    path(OUT), emit: parsed_pileup

    script:
    OUT="${in_bam.baseName}.mpileup.per_base.parsed.txt"
    //TODO: add header    NR==1 { print "#CHROM\\tPOS\\tCOV_MEAN\\tBASEQ_MEAN\\tBASEQ_Q1\\tMAPQ_MEAN\\tMAPQ_Q1" }
    """
    samtools mpileup -A -aa -x --min-BQ 10 --min-MQ 1 --output-MQ \
    --positions ${targets_bed} ${in_bam} | \
    gawk -v OFS='\\t' \
    'function ord(c,i) { \
        for(i=0;i<256;i++){if (sprintf("%c", i) == c) return i} \
        return -10 \
    } \
    { \
        total_non_del=\$4; del_index = index(\$5, "*"); \
        while(del_index!=0) { \
            total_non_del--;  \
            \$5=substr(\$5,1,del_index-1)substr(\$5,del_index+1); \
            \$6=substr(\$6,1,del_index-1)substr(\$6,del_index+1); \
            \$7=substr(\$7,1,del_index-1)substr(\$7,del_index+1); \
            del_index = index(\$5, "*"); \
        }; \
        baseQ=0; mapQ=0; baseQs[1]=0; mapQs[1]=0; \
        for(i=1;i<=\$4;i++) { \
            baseChr=substr(\$6, i, 1); baseQs[i]=ord(baseChr)-33; baseQ+=baseQs[i]; \
            mapChr=substr(\$7,i,1); mapQs[i]=ord(mapChr)-33; mapQ+=mapQs[i]; \
        }; \
        asort(baseQs); asort(mapQs); \
        q1=int((total_non_del+3)/4); \
        if (total_non_del==-1) {print(\$1,\$2,0,0,0,0,0)} \
        else {print(\$1,\$2,total_non_del,baseQ/total_non_del,baseQs[q1],mapQ/total_non_del,mapQs[q1]) }; \
        delete baseQs; delete mapQs; \
    }' - > ${OUT}
    """
}

process add_tract_labels {
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
    cut -f4-10,14 > ${OUT}
    """
}

/*     #label per base
    awk 'BEGIN{OFS="\t"} {print \$1, \$2-1, \$2, \$0}' ${parsed_bam} | \
    bedtools intersect -a - -b  ${targets_bed} -wa -wb | \
    cut -f4-8,12 > ${TEMP} */


