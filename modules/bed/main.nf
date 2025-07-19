process sort_bed {
    //publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    path bed_file

    output:
    path OUT, emit: sorted_bed

    script:
    OUT="${bed_file.baseName}.sorted.bed"
    """
    sort-bed ${bed_file} > ${OUT}
    """
}