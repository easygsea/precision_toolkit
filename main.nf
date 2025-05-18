#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { variant_benchmark } from './workflows/variant_benchmark'
include { signal_correlation } from './workflows/signal_correlation'

def helpMessage() {
    log.info"""
    =========================================
    Clinical Validation Tools v${workflow.manifest.version}
    =========================================

    ====================
    Quick Start Guide
    ====================

    Basic Usage:
        nextflow run main.nf --workflows variant_benchmark,signal_correlation [options]

    ====================
    Workflow Overview
    ====================
    Available Workflows:
        variant_benchmark    Run variant benchmark diagnostic metrics (concordance, sensitivity, precision, f1_score)
        signal_correlation   Run signal (e.g. VAF, log-ratio) correlation analysis
        (more workflows to come...)

    ====================
    Detailed Usage
    ====================
    Variant Benchmark (Diagnostic Metrics) Workflow:
        Mandatory Parameters:
            --truth_dir   Directory containing truth VCF files (must be named as <sample>.truth.vcf or <sample>.truth.vcf.gz)
            --query_dir   Directory containing query VCF files (must be named as <sample>.query.vcf or <sample>.query.vcf.gz)
            --variant_benchmark_engine  Analysis engine: 'happy', 'sompy', or 'wittyer' (default: happy)
            --genome_ref  Required for happy and sompy: Reference genome FASTA

        Optional Parameters:
            --diagnostic_metrics     Diagnostic metrics to calculate (default: 'concordance sensitivity precision f1_score'). Multiple values must be passed as a quoted space-separated list. F1 score does not have a confidence interval.
            --output_dir             Base output directory (default: output_clinical_tools)
            --variant_benchmark_dir  Subdirectory for variant benchmark results (default: variant_benchmark)
            --happy_engine           hap.py engine to use (default: vcfeval) Options: vcfeval, xcmp, scmp-distance, scmp-somatic. Note: vcfeval mode only evaluates PASS variants.
            --happy_options          Additional hap.py options (default: '--write-vcf --write-counts'). Must quote the string and use = to assign the value.
            --sompy_options          Additional som.py options (default: '--include-nonpass'). Must quote the string and use = to assign the value.
            --wittyer_options        Additional witty.er options (default: auto-generated from parameters below). Must quote the string and use = to assign the value.
            --evaluationMode         witty.er parameter: Evaluation mode (default: CrossTypeAndSimpleCounting) Options: CrossTypeAndSimpleCounting, SimpleCounting, GenotypeMatching
            --includedFilters        witty.er parameter: Comma separated list. Only variants contain these filters will be considered. Empty string ('') will include all filters (default: '')
            --percentDistance        witty.er parameter: Maximum allowed distance between truth and query boundaries as fraction of SV length (default: 0.3)
            --bpDistance             witty.er parameter: Maximum allowed distance between truth and query boundaries in base pairs (default: 5000)
            --spurious_variants_vcf  VCF file containing spurious variants to exclude
            --collapse               Collapse option for bcftools isec (default: 'none')
            --skip_raw               Skip raw analysis (only available when spurious_variants_vcf is provided)
            --concordance_tp         Method for defining TP in concordance calculation
                                     Available options:
                                     - 'truth': Use truth set's TP count
                                     - 'query': Use query set's TP count
                                     - 'min': Use minimum of truth and query TP counts (default)
            --decimals               Number of decimal places in rendered output (default: 2)
            --ci_method              Confidence interval method (default: wilson) Options: agresti_coull, beta, binom_test, jeffreys, normal, wilson
            --ci_level               Confidence level for confidence intervals (default: 0.95)

    Signal Correlation Workflow:
        Mandatory Parameters:
            --truth_dir       Directory containing truth VCF files (must be named as <sample>.truth.vcf or <sample>.truth.vcf.gz)
            --query_dir       Directory containing query VCF files (must be named as <sample>.query.vcf or <sample>.query.vcf.gz)
            --truth_signal    Signal name from the truth VCF files e.g. VAF AF LR
            --query_signal    Signal name from the query VCF files e.g. VAF AF LR

        Optional Parameters:
            --spurious_variants_vcf  VCF file containing spurious variants to exclude
            --collapse               Collapse option for bcftools isec (default: 'none')
            --xlim            x-axis limits for the figure (default: "", auto-fit). Example usage: --xlim="0 1"
            --ylim            y-axis limits for the figure (default: "", auto-fit). Example usage: --ylim="0 1"
            --show_regression Whether to show the regression line and equation (default: false)

    ====================
    Resource Management
    ====================
    Resource Adjustment:
        --max_cpus <num_cpus>               # Maximum CPUs per task (default: 16)
        --max_memory <memory_size>          # Maximum memory per task (default: 64.GB)

    SLURM Execution:
        --profile slurm                     # Enable SLURM execution
        --slurm_account <your_account>      # Your SLURM account name (required)
        --slurm_partition <partition_name>  # SLURM partition to use (default: general)
        --slurm_queue <queue_name>          # SLURM queue to use (default: general)

    ====================
    Example Commands
    ====================
    Variant Benchmark with Signal Correlation:
        nextflow run main.nf --workflows variant_benchmark,signal_correlation \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/ \\
            --variant_benchmark_engine happy \\
            --truth_signal VAF \\
            --query_signal AF \\
            --xlim "0 1" \\
            --ylim "0 1" \\
            --output_dir output_clinical_tools

    Variant Benchmark with Spurious Variant Exclusion and hap.py options:
        nextflow run main.nf --workflows variant_benchmark \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/ \\
            --variant_benchmark_engine happy \\
            --spurious_variants_vcf spurious_variants.vcf.gz \\
            --collapse both \\
            --happy_options="--write-vcf --write-counts" \\
            --output_dir output_clinical_tools

    Local Execution with Custom Resources:
        nextflow run main.nf \\
            --max_cpus 8 \\
            --max_memory 32.GB \\
            --workflows variant_benchmark \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/

    SLURM Execution:
        nextflow run main.nf --profile slurm \\
            --slurm_account my_account \\
            --slurm_partition general \\
            --max_cpus 8 \\
            --max_memory 32.GB \\
            --workflows variant_benchmark \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/

    ====================
    Output Structure
    ====================
    <output_dir>/
    └── <variant_benchmark_engine>/
        ├── raw/            # Raw engine reports
        │   ├── happy/      # hap.py raw reports if using happy engine
        │   ├── sompy/      # som.py raw reports if using sompy engine
        │   │   ├── scratch_sompy/ # scratch reports detailing TP/FN/FP calls
        │   └── wittyer/    # witty.er raw reports if using wittyer engine
        │       ├── sample1/
        │       └── sample2/
        ├── curated/        # Curated engine reports (after spurious variant filtering)
        │   ├── happy/      # hap.py curated reports if using happy engine
        │   ├── sompy/      # som.py curated reports if using sompy engine
        │   │   ├── scratch_sompy/ # scratch reports detailing TP/FN/FP calls
        │   └── wittyer/    # witty.er curated reports if using wittyer engine
        │       ├── sample1/
        │       └── sample2/
        ├── diagnostic_metrics_happy_raw_concordance.csv     # Raw variant concordance in CSV
        ├── diagnostic_metrics_happy_curated_concordance.csv # Curated variant concordance in CSV
        ├── diagnostic_metrics_happy_raw_sensitivity.csv     # Raw sensitivity in CSV
        ├── diagnostic_metrics_happy_curated_sensitivity.csv # Curated sensitivity in CSV
        ├── diagnostic_metrics_happy_raw_precision.csv       # Raw precision in CSV
        ├── diagnostic_metrics_happy_curated_precision.csv   # Curated precision in CSV
        ├── diagnostic_metrics_happy_combined.md             # Combined raw/curated diagnostic metrics in Markdown
        └── diagnostic_metrics_happy_combined.docx           # Combined raw/curated diagnostic metrics in Word
    """.stripIndent()
}

// Workflow completion handler
workflow.onComplete {
    log.info"""
    ========================================
    Clinical Tools Analysis Complete!
    ========================================
    Command line    : ${workflow.commandLine}
    Completed at    : ${workflow.complete}
    Duration        : ${workflow.duration}
    Success         : ${workflow.success}
    Exit status    : ${workflow.exitStatus}
    Work directory  : ${workflow.workDir}
    Output directory: ${params.output_dir}
    """

    if (!workflow.success) {
        log.error "Pipeline failed! Check the logs for details."
    }
}

workflow {
    // Default workflow (show help)
    if (!params.workflows) {
        helpMessage()
        exit 0
    } else {
        def workflowList = params.workflows.split(',').collect { it.trim() }
        def validWorkflows = ['variant_benchmark', 'signal_correlation']

        // Validate user-selected workflows
        def invalidWorkflows = workflowList - validWorkflows
        if (invalidWorkflows) {
            error "Unknown workflow(s): ${invalidWorkflows.join(', ')}. Valid options are: ${validWorkflows.join(', ')}"
        }

        // Run user-selected workflows
        workflowList.each { workflow -> "$workflow"() }
    }
}
