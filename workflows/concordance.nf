#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Variant concordance analysis engine enum
enum VariantConcordanceEngine {
    happy, wittyer
}

// Function to validate engine selection
def validate_engine_selection(engine) {
    def valid_engines = VariantConcordanceEngine.values()*.toString()
    if (!(engine in valid_engines)) {
        throw new IllegalArgumentException(
            "Invalid 'variant_concordance_engine': ${engine}. " +
            "Valid options are: ${valid_engines.join(', ')}"
        )
    }
}

include { variant_concordance_workflow } from '../subworkflows/concordance'

workflow concordance {
    validate_engine_selection(params.variant_concordance_engine)
    variant_concordance_workflow()
}
