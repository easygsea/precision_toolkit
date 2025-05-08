// Utility module for shared functions

/**
 * Builds channels for paired VCF files from truth and query directories.
 *
 * @param truth_dir   Directory containing truth VCF files.
 * @param query_dir   Directory containing query VCF files.
 * @return            Channel of tuples containing sample name, truth VCF, and query VCF.
 */
def build_vcf_pair_channels(truth_dir, query_dir) {
    return Channel
        .fromPath("${truth_dir}/*.{vcf,vcf.gz}")
        .map { truth_vcf ->
            def sampleName = truth_vcf.getName().replaceFirst(/\..*$/, "")
            def query_vcf = file("${query_dir}/${sampleName}.*.vcf.gz") ?:
                            file("${query_dir}/${sampleName}.*.vcf")
            return tuple(sampleName, truth_vcf, query_vcf)
        }
}
