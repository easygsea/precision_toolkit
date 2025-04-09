process bgzip_vcf {
    input:
    path original_vcf

    output:
    path("${original_vcf}.gz"), emit: gzipped_vcf

    script:
    """
    bgzip -c "${original_vcf}" > "${original_vcf}.gz"
    """
}

process index_vcf {
    input:
    path gzipped_vcf

    output:
    path("${gzipped_vcf}.tbi"), emit: indexed_vcf

    script:
    """
    tabix -p vcf "${gzipped_vcf}"
    """
}

process normalize_vcf {
    tag "${vcf}"

    input:
    path vcf
    path vcf_tbi

    output:
    path("${vcf}.normalized.vcf.gz"), emit: normalized_vcf

    script:
    """
    # Normalize VCF
    bcftools norm -m -any "${vcf}" -o "${vcf}.normalized.vcf.gz"
    """
}
