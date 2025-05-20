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

process exclude_spurious_variants {
    tag "${sampleName}"

    input:
    tuple val(sampleName), path(original_vcf)
    path normalized_spurious_vcf
    path normalized_spurious_vcf_tbi
    val label
    val collapse // collapse option for bcftools isec

    output:
    tuple val(sampleName), path("${sampleName}.${label}.no_spurious.vcf.gz"), emit: no_spurious_vcf

    script:
    """
    # Check and compress original VCF if needed
    if [[ "${original_vcf}" != *.gz ]]; then
        bgzip -c "${original_vcf}" > "${original_vcf}.gz"
        compressed_vcf="${original_vcf}.gz"
    else
        compressed_vcf="${original_vcf}"
    fi

    # Index original VCF if needed
    if [[ ! -f "\${compressed_vcf}.tbi" ]]; then
        tabix -p vcf "\${compressed_vcf}"
    fi

    # Normalize and decompose multiallelic variants in original VCF
    bcftools norm -m -any "\${compressed_vcf}" -o normalized_original.vcf.gz

    # Index normalized original VCF
    tabix -p vcf normalized_original.vcf.gz

    # Perform variant exclusion using bcftools isec on normalized VCFs
    bcftools isec --collapse "${collapse}" --complement --write 1 --output-type z \
        --output "${sampleName}.${label}.no_spurious.vcf.gz" normalized_original.vcf.gz "${normalized_spurious_vcf}"
    """
}
