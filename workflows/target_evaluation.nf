#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Include the gene_target_evaluation_workflow
include { gene_target_evaluation_workflow } from '../subworkflows/target_evaluation/main'

workflow target_evaluation {
    gene_target_evaluation_workflow()
}
