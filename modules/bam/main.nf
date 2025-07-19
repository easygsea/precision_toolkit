process index_bam_file {
    //publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path bam_file

    output:
    path OUT, emit: bam_index

    script:
    OUT="${bam_file.baseName}.bai"
    """
    samtools index ${bam_file} -o ${OUT}
    """
}