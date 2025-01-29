#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { concordance } from './modules/concordance'

def helpMessage() {
    log.info"""
    =========================================
    Clinical Validation Tools v${workflow.manifest.version}
    =========================================

    Usage:
        nextflow run clinical_tools.nf --workflows <workflow1,workflow2,...> [options]

    Available Workflows:
        concordance    Run variant concordance analysis
        (more workflows to come...)

    Concordance Workflow Arguments:
        Mandatory:
            --truth_dir   Directory containing truth VCF files
            --query_dir   Directory containing query VCF files
            --variant_concordance_engine  Analysis engine: 'happy' or 'wittyer' (default: happy)

        Optional:
            --genome_ref             Reference genome FASTA (required for happy)
            --output_dir              Base output directory (default: output_clinical_tools)
            --concordance_dir         Subdirectory for concordance results (default: concordance)
            --happy_options         Additional options for hap.py
            --wittyer_options       Additional options for witty.er
            --spurious_variants_vcf  VCF file containing spurious variants to exclude
            --force                 Overwrite existing output directory

    General Options:
        --help          Show this help message

    Examples:
        # Run concordance workflow
        nextflow run clinical_tools.nf --workflows concordance \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/ \\
            --variant_concordance_engine happy \\
            --output_dir output_clinical_tools

        # Run concordance with spurious variant exclusion
        nextflow run clinical_tools.nf --workflows concordance \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/ \\
            --variant_concordance_engine happy \\
            --spurious_variants_vcf spurious_variants.vcf.gz \\
            --output_dir output_clinical_tools

        # Run multiple workflows
        nextflow run clinical_tools.nf --workflows concordance,sensitivity,specificity \\
            --truth_dir truth_vcfs/ \\
            --query_dir query_vcfs/

    Output Structure:
        <output_dir>/
        └── <concordance_dir>/
            ├── happy/          # hap.py results if using happy engine
            ├── wittyer/        # witty.er results if using wittyer engine
            ├── variant_concordance_combined.csv  # Combined raw/curated concordance in CSV
            ├── variant_concordance_combined.md   # Combined raw/curated concordance in Markdown
            └── variant_concordance_combined.docx # Combined raw/curated concordance in Word
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
