process INDEX_BAM_FILE {
    tag "${sample_name}"

    input:
    tuple val(sample_name), path(bam_file), val(pool)

    output:
    path OUT, emit: bam_index

    script:
    OUT="${bam_file.baseName}.bai"
    """
    samtools index ${bam_file} -o ${OUT}
    """
}
