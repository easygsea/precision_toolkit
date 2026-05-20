#!/usr/bin/env nextflow

nextflow.enable.dsl=2

enum NormalizationMethod {
    mean, median
}

def validate_normalization_method(method) {
    def valid = NormalizationMethod.values()*.toString()
    if (!(method in valid)) {
        throw new IllegalArgumentException(
            "Invalid normalization_method: ${method}. " +
            "Valid options: ${valid.join(', ')}"
        )
    }
}

// Include the gene_target_evaluation_workflow
include { gene_target_evaluation_workflow } from '../subworkflows/target_evaluation/main'

workflow target_evaluation {
    validate_normalization_method(params.normalization_method)
    gene_target_evaluation_workflow()
}
