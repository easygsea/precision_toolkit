process SORT_BED {
    input:
    path bed_file

    output:
    path OUT, emit: sorted_bed

    script:
    OUT="${bed_file.baseName}.sorted.bed"
    """
    bedops sort-bed ${bed_file} > ${OUT}
    """
}
