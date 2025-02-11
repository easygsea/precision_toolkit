#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { concordance } from './modules/concordance'

def helpMessage() {
    log.info"""
    =========================================
    Clinical Validation Tools v${workflow.manifest.version}
    =========================================

    ====================
    Quick Start Guide
    ====================
    
    Basic Usage:
        nextflow run clinical_tools.nf --workflows <workflow1,workflow2,...> [options]
    
    ====================
    Workflow Overview
    ====================
    Available Workflows:
        concordance    Run variant concordance analysis
        (more workflows to come...)
    
    ====================
    Detailed Usage
    ====================
    Concordance Workflow:
        Mandatory Parameters:
            --truth_dir   Directory containing truth VCF files (must be named as <sample>.truth.vcf or <sample>.truth.vcf.gz)
            --query_dir   Directory containing query VCF files (must be named as <sample>.query.vcf or <sample>.query.vcf.gz)
            --variant_concordance_engine  Analysis engine: 'happy' or 'wittyer' (default: happy)
        
        Optional Parameters:
            --genome_ref             Reference genome FASTA (required for happy)
            --output_dir             Base output directory (default: output_clinical_tools)
            --concordance_dir        Subdirectory for concordance results (default: concordance)
            --happy_options          Additional options for hap.py
            --wittyer_options        Additional options for witty.er
            --spurious_variants_vcf  VCF file containing spurious variants to exclude
            --collapse               Collapse option for bcftools isec (default: 'none')
            --skip_raw               Skip raw analysis (only available when spurious_variants_vcf is provided)
    
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
    Basic Concordance:
        nextflow run clinical_tools.nf --workflows concordance \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/ \\
            --variant_concordance_engine happy \\
            --output_dir output_clinical_tools
    
    Concordance with Spurious Variant Exclusion:
        nextflow run clinical_tools.nf --workflows concordance \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/ \\
            --variant_concordance_engine happy \\
            --spurious_variants_vcf spurious_variants.vcf.gz \\
            --collapse both \\
            --output_dir output_clinical_tools
    
    Multiple Workflows:
        nextflow run clinical_tools.nf --workflows concordance,sensitivity,specificity \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/
    
    Local Execution with Custom Resources:
        nextflow run clinical_tools.nf \\
            --max_cpus 8 \\
            --max_memory 32.GB \\
            --workflows concordance \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/
    
    SLURM Execution:
        nextflow run clinical_tools.nf --profile slurm \\
            --slurm_account my_account \\
            --slurm_partition general \\
            --max_cpus 8 \\
            --max_memory 32.GB \\
            --workflows concordance \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/
    
    ====================
    Output Structure
    ====================
    <output_dir>/
    └── <concordance_dir>/
        ├── raw/            # Raw engine reports
        │   ├── happy/      # hap.py raw reports if using happy engine
        │   └── wittyer/    # witty.er raw reports if using wittyer engine
        │       ├── sample1/
        │       └── sample2/
        ├── curated/        # Curated engine reports (after spurious variant filtering)
        │   ├── happy/      # hap.py curated reports if using happy engine
        │   └── wittyer/    # witty.er curated reports if using wittyer engine
        │       ├── sample1/
        │       └── sample2/
        ├── variant_concordance_happy_raw.csv       # Raw concordance in CSV
        ├── variant_concordance_happy_curated.csv   # Curated concordance in CSV
        ├── variant_concordance_happy_combined.md   # Combined raw/curated concordance in Markdown
        └── variant_concordance_happy_combined.docx # Combined raw/curated concordance in Word
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
        def validWorkflows = ['concordance']
        
        // Validate user-selected workflows
        def invalidWorkflows = workflowList - validWorkflows
        if (invalidWorkflows) {
            error "Unknown workflow(s): ${invalidWorkflows.join(', ')}. Valid options are: ${validWorkflows.join(', ')}"
        }
        
        // Run user-selected workflows
        workflowList.each { workflow -> "$workflow"() }
    }
}
