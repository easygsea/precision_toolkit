#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { variant_benchmark } from './workflows/variant_benchmark'
include { signal_correlation } from './workflows/signal_correlation'
include { target_evaluation } from './workflows/target_evaluation'

def helpMessage() {
    log.info"""
    =========================
    Clinical Validation Tools
    =========================

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
        target_evaluation    Run target evaluation to generate per-base coverage, MAPQ, and BASEQ metrics for target space
        (more workflows to come...)

    ====================
    Detailed Usage
    ====================
    Variant Benchmark (Diagnostic Metrics) Workflow:
        Mandatory Parameters:
            --truth_dir   Directory containing truth VCF files (must be named as <sample>.truth.vcf or <sample>.truth.vcf.gz)
            --query_dir   Directory containing query VCF files (must be named as <sample>.query.vcf or <sample>.query.vcf.gz)
            --variant_benchmark_engine  Analysis engine: 'happy', 'sompy', or 'wittyer' (default: happy)
            --genome_ref  Required for happy: Reference genome FASTA

        Optional Parameters:
            --diagnostic_metrics     Diagnostic metrics to calculate (default: 'concordance sensitivity precision f1_score'). Multiple values must be passed as a quoted space-separated list. F1 score does not have a confidence interval.
            --output_dir             Base output directory (default: output_clinical_tools)
            --variant_benchmark_subdir  Subdirectory for variant benchmark results (default: variant_benchmark)
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
            --skip_raw               Skip raw analysis (only available when spurious_variants_vcf is provided) (flag)
            --concordance_tp         Method for defining TP in concordance calculation
                                     Available options:
                                     - 'truth': Use truth set's TP count
                                     - 'query': Use query set's TP count
                                     - 'min': Use minimum of truth and query TP counts (default)
            --decimals               Number of decimal places in rendered output (default: 2)
            --ci_method              Confidence interval method (default: wilson) Options: agresti_coull, beta, binom_test, jeffreys, normal, wilson
            --ci_level               Confidence level for confidence intervals (default: 0.95)
            --include_all_data_csv   Option to output compiled csv for data wrangling/plotting (flag)

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
            --filter_source   FILTER column to use for coloring ('', 'truth', or 'query') (default: '')

    Target Evaluation Workflow:
        Mandatory Parameters:
            --aligned_files                 Glob expression matching one or more bam/cram file paths. Any non-bam/cram
                                            files are ignored. If any cram provided, also provide --genome-ref for
                                            expansion. Example usage: 'path/to/dir/*.{bam,cram,bai}'
            --targets_bed                   BED file of genomic targets

        Optional Parameters:
            --target_evaluation_subdir      Subdirectory for target evaluation results (default: target_evaluation)
            --output_raw_mpileup            Flag to output raw/un-parsed mpileup file (note that this file is large)
            --normalize_coverage            If set, coverage across the targets bed for every sample is normalized and scaled to center on this value
            --genome_ref                    Reference genome for CRAM files. CRAM files skipped if not provided.
            --visualize                     Flag to generate per-target plots for all input files per stat

        Fine-Tuning Parameters:
            --coverage_threshold                    Minimum acceptable coverage per base (default: 25)
            --baseq_threshold                       Minimum acceptable first-quartile(Q1) of BASEQ scores per base (default: 30)
            --mapq_threshold                        Minimum acceptable first-quartile(Q1) of MAPQ scores per base (default: 30)
            --read_fail_tolerance                   Maximum tolerable percentage of reads per base failing baseq and mapq thresholds (default: 0.25)
            --target_fail_tolerance                 Maximum tolerable percentage of bases failed for target-level PASS per sample (default: 0.25)
            --base_fail_tolerance                   Maximum tolerable percentage of libraries failing at a base for base-level PASS across all libraries (default: 0.25)
            --tract_gap_tolerance                   Maximum gap tolerance between fail regions when building tracts (default: 2)
            --min_bq_per_read.coverage_analysis     Minimum BASEQ for read to be included in coverage count at each position (default: 10)
            --min_bq_per_read.mapq_analysis         Minimum BASEQ for read to be included in MAPQ Q1 analysis at each position (default: 10)
            --min_bq_per_read.baseq_analysis        Minimum BASEQ for read to be included in BASEQ Q1 analysis at each position (default: 0)
            --min_mq_per_read.coverage_analysis     Minimum MAPQ for read to be included in coverage count at each position (default: 1)
            --min_mq_per_read.mapq_analysis         Minimum MAPQ for read to be included in MAPQ Q1 analysis at each position (default: 0)
            --min_mq_per_read.baseq_analysis        Minimum MAPQ for read to be included in BASEQ Q1 analysis at each position (default: 1)

    ====================
    Resource Management
    ====================
    Resource Adjustment:
        --max_cpus <num_cpus>               # Maximum CPUs per task (default: 16)
        --max_memory <memory_size>          # Maximum memory per task (default: 64.GB)

    SLURM Execution:
        --profile slurm                     # Enable SLURM execution
        --slurm_account <your_account>      # Your SLURM account name
        --slurm_queue <queue_name>          # SLURM partition to use (default: general)

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
        def validWorkflows = ['variant_benchmark', 'signal_correlation', 'target_evaluation']

        // Validate user-selected workflows
        def invalidWorkflows = workflowList - validWorkflows
        if (invalidWorkflows) {
            error "Unknown workflow(s): ${invalidWorkflows.join(', ')}. Valid options are: ${validWorkflows.join(', ')}"
        }

        // Run user-selected workflows
        workflowList.each { workflow -> "$workflow"() }
    }
}
