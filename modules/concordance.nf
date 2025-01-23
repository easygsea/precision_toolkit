#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Variant concordance analysis engine enum
enum VariantConcordanceEngine {
    happy, wittyer
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