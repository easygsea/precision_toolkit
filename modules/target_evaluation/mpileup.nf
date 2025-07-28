process get_per_base_stats {
    label "dynamic_resource"
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    // Current specs used here:
    // 1, output all positions in bed file
    // 2. Min BQ of 10 consider BQ in calculations (ref old) (TODO: pass in values, with default here, caveat 0 for baseq in docs)
    // 3. Min MQ of 1 (ref old)
    // 4. -A count anomalous reads pairs -x turn off overlaps removal
    // 5. custom gawk to adjust for deletions & parse

    input:
    path(targets_bed)
    tuple path(in_bam), val(pool_id)

    output:
    tuple path(OUT), val(pool_id), emit: parsed_pileup
    // Example Output: chr1	17371254	570	63	52	60	60	IX00000

    script:
    OUT="${in_bam.baseName}.mpileup.per_base.parsed.txt"
    """
    samtools mpileup -A -aa -x --min-BQ 10 --min-MQ 1 --output-MQ \
    --positions ${targets_bed} ${in_bam} | \
    gawk -v OFS='\\t' \
    'function ord(c,i) { \
        for(i=0;i<256;i++){if (sprintf("%c", i) == c) return i} \
        return -10 \
    } \
    BEGIN { print "#CHROM","POS","COVERAGE","BASEQ_MED","BASEQ_Q1","MAPQ_MED","MAPQ_Q1","POOL" } \
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
            baseChr=substr(\$6, i, 1); baseQs[i]=ord(baseChr)-33; \
            mapChr=substr(\$7,i,1); mapQs[i]=ord(mapChr)-33; \
        }; \
        asort(baseQs); asort(mapQs); \
        median=int(total_non_del/2); \
        q1=int((total_non_del+3)/4); \
        if (total_non_del==-1) {print(\$1,\$2,0,0,0,0,0,"${pool_id}")} \
        else {print(\$1,\$2,total_non_del,baseQs[median],baseQs[q1],mapQs[median],mapQs[q1],"${pool_id}")} \
        delete baseQs; delete mapQs; \
    }' - > ${OUT}
    """
}
//        else {print(\$1,\$2,total_non_del,baseQ/total_non_del,baseQs[q1],mapQ/total_non_del,mapQs[q1]) }; \



