#!/usr/bin/env nextflow

nextflow.enable.dsl=2

//add any variable enums here
    //this is a collection of variables grouped under collection, which has specific funtions like .values()
    //this can be called like collection.variable


// Include the gene_target_evaluation_workflow
include { gene_target_evaluation_workflow } from '../subworkflows/target_evaluation/main'

workflow gene_target_evaluation {
    gene_target_evaluation_workflow()
}