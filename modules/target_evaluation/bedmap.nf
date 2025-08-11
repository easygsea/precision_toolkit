
// not currently in development due to logic error in existing script

process build_per_base_bed {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path targets_bed_path

    output:
    path OUT, emit: per_base_bed

    script:
    OUT="${targets_bed_path.baseName}.per_base.bed"
    """
    build_per_base_bed --input_bed ${targets_bed_path} --output_bed ${OUT}
    """
}


process get_per_base_depth {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'
    cpus 16

    input:
    path bed_file
    path bam_file
    path bam_index_file

    output:
    path OUT, emit: per_base_stats

    script:
    OUT="${bam_file.baseName}.per_base_depth.txt"
    """
    samtools depth --min-BQ 10 --min-MQ 1 -a -b ${bed_file} -@ ${task.cpus} ${bam_file} > $OUT
    """

}

process convert_bam_to_bed {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path bam_file

    output:
    path OUT, emit: converted_bam

    script:
    OUT="${bam_file.baseName}.converted_bam.bed"
    """
    bam2bed < ${bam_file} > ${OUT}
    """
}

process convert_to_baseq_scores {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path converted_bam

    output:
    path OUT, emit: converted_baseq_bam

    script:
    OUT="${converted_bam.baseName}.baseq.bed"

    script:
    """
    awk -v FS="\t" -v OFS="\t" \
    'BEGIN { for (n=0; n<256; n++) ord[sprintf("%c",n)]=n }
    {
        old=\$5; l=split(\$13,q,""); s=0; \
        for(n=1; n<=l; n++) { s+=ord[q[n]]-33; } \
        \$5=s/l; \$13=old; print \$0; \
    }' ${converted_bam} > ${OUT}
    """
}

process get_per_base_stats_with_bedmap {
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path sorted_per_base_bed
    path converted_bam
    val score_type

    output:
    path OUT, emit: scored_bed

    script:
    OUT="${converted_bam.baseName}.${score_type}_scored.bed"

    script:
    """
    #score a bam file's alignment's mapq scores for given regions
    #best to use subset bam since we are converting bam to bed and it will be a huge file otherwise

    bedmap \
    --delim '\t' \
    --echo \
    --count \
    --min \
    --mean \
    --median \
    --stdev \
    --variance \
    --tmean 0.05 0.05 \
    --tmean 0.05 0 \
    --kth 0.25 \
    ${sorted_per_base_bed} \
    ${converted_bam} \
    > ${OUT}

    #Generalized  median.  Report  the  value, x, such that the fraction <val> of overlapping elements' scores from <map-file> is less than x, and the fraction 1-<val> of scores is greater than x.  0  < val <= 1.
    """

}

//not used -- what is the point of this?
process get_per_read_mapq {
    //TODO: remove publish
    publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path bam_file
    path bai_file

    output:
    path OUT, emit: mapq_values

    script:
    OUT="${bam_file.baseName}.per_base_mapq.txt"
    """
        #remove supplementary alignments (only primary and secondary)
        #takes only the mapq and and read id
        samtools view -F 2048 ${bam_file} | cut -f1,5 > $OUT
    """
}
