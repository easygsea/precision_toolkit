//include these processes, functions, or named workflows as defined in modules
include {
    subset_bam
    get_mapq_from_bam
    get_baseq
    measure_per_base_depth
} from '../../modules/target_evaluation/main'


// Main variant gene target evaluation workflow
workflow gene_target_evaluation_workflow {
    main:
        // Validate input directories/files
        if (!file(params.truth_dir).exists()) error "Truth directory not found: ${params.truth_dir}"
        if (!file(params.query_dir).exists()) error "Query directory not found: ${params.query_dir}"


        subset_bam
        get_mapq_from_bam
        get_baseq
        measure_per_base_depth


}