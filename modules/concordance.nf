#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Variant concordance analysis engine enum
enum VariantConcordanceEngine {
    happy, wittyer
}

// Module parameters
params {
    // Input parameters
    truth_dir = null // directory containing truth VCFs
    query_dir = null // directory containing query VCFs
    variant_concordance_engine = "happy" // default happy
    happy_options = '--write-vcf --write-counts' // default options for happy
    wittyer_options = '' // default options for wittyer, if any
}

// Validate engine selection
def valid_engines = VariantConcordanceEngine.values()*.toString()
if (!(params.variant_concordance_engine in valid_engines)) {
    throw new IllegalArgumentException(
        "Invalid 'variant_concordance_engine': ${params.variant_concordance_engine}. " +
        "Valid options are: ${valid_engines.join(', ')}"
    )
}

include { variant_concordance_workflow } from '../workflows/variant_concordance'

workflow concordance {
    variant_concordance_workflow()
}