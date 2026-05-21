#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { validate_enum_value } from '../modules/utils'

enum NormalizationMethod {
    mean, median
}

def validate_normalization_method(method) {
    validate_enum_value([method], NormalizationMethod)
}

// Include the gene_target_evaluation_workflow
include { gene_target_evaluation_workflow } from '../subworkflows/target_evaluation'

workflow target_evaluation {
    validate_normalization_method(params.normalization_method)
    gene_target_evaluation_workflow()
}
