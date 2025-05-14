include {
    build_per_base_bed
    measure_per_base_depth
    //gather_bed
    //filter_low_scoring_tracts
} from '../../modules/target_evaluation/main'

//mpileup tool
include {
    get_per_base_stats
    get_per_tract_stats
} from '../../modules/target_evaluation/mpileup'

params.tool = "main"

// Main variant gene target evaluation workflow
workflow gene_target_evaluation_workflow {
    main:
        // Validate input directories/files
        if (!file("${params.targets_bed}").exists()) error "Target bed not found: ${params.targets_bed}"
        if (!file(params.bams_dir).exists()) error "Bams dir not found: ${params.bams_dir}"

        bams_channel = channel.fromPath("${params.bams_dir}/*.bam").view()
        //can use checkIfExists to output error for empty directory

        if (params.tool == "mpileup") {
            get_per_base_stats(params.targets_bed, bams_channel)
            get_per_tract_stats(params.targets_bed)

        }

        else {
            // check for existing per-base bed file
            if (!file("${params.targets_bed}.per-base.bed")){
                build_per_base_bed(params.targets_bed) }
             //get_per_base()
                //gather_bam
                //gather_bed
        }

        //after files are compiled, do compiling
        //filter_low_scoring_tracts()




        """
        --mapq_threshold                Minimum acceptable first quartile (Q1) of the MAPQ scores of mapped reads
                                            per base,default is 30
            --baseq_threshold               Minimum acceptable first quartile (Q1) of the BASEQ scores of mapped reads
                                            per base, default is 30
            --normalize_to_mean_coverage    Bam files will be normalized to the provided mean coverage
            --coverage_threshold
        """
}