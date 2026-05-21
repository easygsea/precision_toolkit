#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include {
    validate_enum_value
    get_enum_valid_values
} from '../modules/utils'

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
    validate_enum_value([engine], VariantConcordanceEngine)
}

// Function to validate diagnostic metrics selection
def validate_metrics_selection(metrics) {
    validate_enum_value(metrics.split(' '), DiagnosticMetrics)
}

// Function to validate hap.py engine selection
def validate_happy_engine(engine) {
    if (engine.contains('_')) {
        throw new IllegalArgumentException(
            "Invalid 'happy_engine': ${engine}. " +
            "Engine name cannot contain underscores. " +
            "Valid options are: ${get_enum_valid_values(HappyEngine).join(', ')}"
        )
    }
    def normalized_engine = engine.replace('-', '_')
    validate_enum_value([normalized_engine], HappyEngine)
}

// Function to validate TP method selection
def validate_tp_method(tp) {
    validate_enum_value([tp], ConcordanceTPMethod)
}

// Function to validate confidence interval method
def validate_ci_method(method) {
    validate_enum_value([method], ConfidenceIntervalMethod)
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
