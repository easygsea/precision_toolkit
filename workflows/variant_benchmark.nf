#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Variant concordance analysis engine enum
enum VariantConcordanceEngine {
    happy, sompy, truvari, wittyer
}

// Diagnostic metrics enum
enum DiagnosticMetrics {
    concordance, sensitivity, precision, f1_score
}

// Concordance TP method enum
enum ConcordanceTPMethod {
    truth, query, min
}

// hap.py engine enum
enum HappyEngine {
    vcfeval, xcmp, scmp_distance, scmp_somatic
}

// Confidence interval method enum
enum ConfidenceIntervalMethod {
    agresti_coull, beta, binom_test, jeffreys, normal, wilson
}

def validate_genome_ref(genome_ref) {
    if (!file(genome_ref).exists()) {
        throw new IllegalArgumentException(
            "Invalid 'genome_ref': ${genome_ref}. " +
            "File does not exist."
        )
    }
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

// Function to validate hap.py engine selection
def validate_happy_engine(engine) {
    def valid_engines = HappyEngine.values()*.toString()
    def normalized_engine = engine.replace('-', '_')
    if (engine.contains('_')) {
        throw new IllegalArgumentException(
            "Invalid 'happy_engine': ${engine}. " +
            "Engine name cannot contain underscores. " +
            "Valid options are: ${valid_engines.join(', ')}"
        )
    }
    if (!(normalized_engine in valid_engines)) {
        throw new IllegalArgumentException(
            "Invalid 'happy_engine': ${engine}. " +
            "Valid options are: ${valid_engines.join(', ')}"
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

// Function to validate confidence interval method
def validate_ci_method(method) {
    def valid_methods = ConfidenceIntervalMethod.values()*.toString()
    if (!(method in valid_methods)) {
        throw new IllegalArgumentException(
            "Invalid 'confidence_interval_method': ${method}. " +
            "Valid options are: ${valid_methods.join(', ')}"
        )
    }
}

include { prepare_variant_benchmark_inputs } from '../subworkflows/prepare_variant_benchmark_inputs/main'
include { variant_benchmark_workflow } from '../subworkflows/variant_benchmark/main'

workflow variant_benchmark {
    validate_engine_selection(params.variant_benchmark_engine)
    validate_metrics_selection(params.diagnostic_metrics)
    validate_happy_engine(params.happy_engine)
    validate_tp_method(params.concordance_tp)
    validate_ci_method(params.ci_method)
    if (params.variant_benchmark_engine in ['happy', 'sompy', 'truvari']) {
        validate_genome_ref(params.genome_ref)
    }
    def variant_benchmark_inputs = prepare_variant_benchmark_inputs()
    variant_benchmark_workflow(
        variant_benchmark_inputs.vcf_pairs,
        variant_benchmark_inputs.vcf_tbi_pairs,
        variant_benchmark_inputs.curated_vcf_pairs,
        variant_benchmark_inputs.curated_vcf_tbi_pairs,
    )
}
