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
    samtools mpileup -A -a -x --min-BQ 10 --min-MQ 1 --output-MQ --positions ${targets_bed} ${in_bam} | \
    gawk '
        BEGIN{OFS="\t"}
        function ord(c,i) { for(i=0;i<256;i++) {if (sprintf("%c", i) == c) return i} return -1 } {
            baseQ=0; mapQ=0;
            for(i=1;i<=\$4;i++) {
                baseChr = substr(\$6, i, 1);
                baseQ+=ord(baseChr)-33;
                mapChr=substr(\$7,i,1);
                mapQ+=ord(mapChr)-33;};
            print(\$1,\$2,\$4,baseQ/\$4,mapQ/\$4) }' - > $OUT
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
    OUT="${parsed_bam}.mpileup.parsed.labelled.per-base "
    """
    awk 'BEGIN{OFS="\t"} {print \$1, \$2-1, \$2, \$0}' ${parsed_bam} | \
    bedtools intersect -a - -b  ${targets_bed} -wa -wb | \
    cut -f4-8,12 > $OUT
    """
    //ignore chimeric reads
}
