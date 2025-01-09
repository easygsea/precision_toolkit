#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include {
    variant_concordance_workflow
} from './workflows/variant_concordance.nf'

workflow {
    variant_concordance_workflow()
}
