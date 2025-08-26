process SORT_BED {
    input:
    path bed_file

    output:
    path OUT, emit: sorted_bed

    script:
    OUT="${bed_file.baseName}.sorted.bed"
    """
    bedtools sort -i ${bed_file} > ${OUT}
    """
}
