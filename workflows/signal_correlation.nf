#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { signal_correlation_workflow } from '../subworkflows/signal_correlation'

// Define the workflow
workflow signal_correlation {
    signal_correlation_workflow()
}
