process generate_fai {
    tag "${genome_ref}"

    input:
    path genome_ref

    output:
    path("${genome_ref}.fai"), emit: genome_fai

    script:
    """
    samtools faidx "${genome_ref}"
    """
}
