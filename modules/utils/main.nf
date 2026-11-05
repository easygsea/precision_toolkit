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
            def sample_name = truth_vcf.getName().replaceFirst(/\..*$/, "")
            def query_vcf = file("${query_dir}/${sample_name}.*.vcf.gz") ?:
                            file("${query_dir}/${sample_name}.*.vcf")
            return tuple(sample_name, truth_vcf, query_vcf[0])
        }
}


/**
 * Throws an error if the given value is not a valid enum in the given enum class.
 *
 * @param value_array   The values to validate.
 * @param valid_enum_class   The valid enum class to check against.
 * @return            Throws an IllegalArgumentException if the value is not valid.
 */
def validate_enum_value(value_array, valid_enum_class) {
    def valid = get_enum_valid_values(valid_enum_class)
    if (!value_array.every { it in valid }) {
        throw new IllegalArgumentException(
            "Invalid value: ${value_array}. " +
            "Valid options: ${valid.join(', ')}"
        )
    }
}

/**
 * Returns a list of valid enum values for a given enum class.
 *
 * @param valid_enum_class   The valid enum class to parse.
 * @return            A list of string of valid enum values.
 */
def get_enum_valid_values(valid_enum_class) {
    return valid_enum_class.values()*.toString()
}
