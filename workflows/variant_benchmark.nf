#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Variant concordance analysis engine enum
enum VariantConcordanceEngine {
    happy, wittyer
}

// Diagnostic metrics enum
enum DiagnosticMetrics {
    concordance, sensitivity, precision, f1_score
}

// Concordance TP method enum
enum ConcordanceTPMethod {
    truth, query, min
}

// Function to validate engine selection
def validate_engine_selection(engine) {
    def valid_engines = VariantConcordanceEngine.values()*.toString()
    if (!(engine in valid_engines)) {
        throw new IllegalArgumentException(
            "Invalid 'variant_benchmark_engine': ${engine}. " +
            "Valid options are: ${valid_engines.join(', ')}"
        )
    }
}

// Function to validate diagnostic metrics selection
def validate_metrics_selection(metrics) {
    def valid_metrics = DiagnosticMetrics.values()*.toString()
    def metricsList = metrics.split(' ')
    if (!metricsList.every { it in valid_metrics }) {
        throw new IllegalArgumentException(
            "Invalid 'diagnostic_metrics': ${metrics}. " +
            "Valid options are: ${valid_metrics.join(', ')}"
        )
    }
}

// Function to validate TP method selection
def validate_tp_method(tp) {
    def valid_tp_methods = ConcordanceTPMethod.values()*.toString()
    if (!(tp in valid_tp_methods)) {
        throw new IllegalArgumentException(
            "Invalid 'concordance_tp': ${tp}. " +
            "Valid options are: ${valid_tp_methods.join(', ')}"
        )
    }
}

// Include the variant benchmark subworkflow
include { variant_benchmark_workflow } from '../subworkflows/variant_benchmark/main'

workflow variant_benchmark {
    validate_engine_selection(params.variant_benchmark_engine)
    validate_metrics_selection(params.diagnostic_metrics)
    validate_tp_method(params.concordance_tp)
    variant_benchmark_workflow()
}
