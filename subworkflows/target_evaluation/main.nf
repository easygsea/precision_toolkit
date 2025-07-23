include {
    get_per_tract_stats
    //filter_low_scoring_tracts
    filter_low_scoring_bases
} from '../../modules/target_evaluation/main'

//bedmap tool (not currently being developed)
include {
    build_per_base_bed
    convert_bam_to_bed
    get_per_base_depth
    get_per_base_stats_with_bedmap as extract_per_base_mapq_with_bedmap
    get_per_base_stats_with_bedmap as extract_per_base_baseq_with_bedmap
    convert_to_baseq_scores
} from '../../modules/target_evaluation/bedmap'

include {
    get_per_base_stats
    add_tract_labels
} from '../../modules/target_evaluation/mpileup'

include { index_bam_file as index_bam_files } from '../../modules/bam/main'
include { sort_bed } from '../../modules/bed/main'

//TODO: delete
params.tool = "mpileup"

//TODO: valid input checks function
// def verify_input() {
//     if (!file("${params.targets_bed}").exists()) error "Target bed not found: ${params.targets_bed}"
//     if (!file(params.bams_dir).exists()) error "Bams dir not found: ${params.bams_dir}"
// }

// Main variant gene target evaluation workflow
workflow gene_target_evaluation_workflow {
    main:

        // Validate input directories/files
        //if (!file("${params.targets_bed}").exists()) error "Target bed not found: ${params.targets_bed}"
        //if (!file(params.bams_dir).exists()) error "Bams dir not found: ${params.bams_dir}"

        //build channel with bam files
        bam_ch = channel.fromPath(params.bams_dir)
        //bam_ch = channel.fromPath("${params.bams_dir}/*.bam")
        bam_ch.view{item -> "BAMS_CH: $item"}
        //todo: del
        println "TARGETS BED: ${params.targets_bed}"


        // 0. Setup
        sort_bed(file(params.targets_bed))
        index_bam_files(bam_ch)

        //Option a: using mpileup
        if (params.tool == "mpileup") {
            get_per_base_stats(sort_bed.out.sorted_bed, bam_ch)
            add_tract_labels(sort_bed.out.sorted_bed, get_per_base_stats.out.parsed_pileup)
        }
        //Option b: using samtools depth (not currently in development -- ignore)
        else { }

        //after files are compiled, score bases on thresholds
        filter_low_scoring_bases (
            add_tract_labels.out.labelled_pileup,
            params.coverage_threshold,
            params.baseq_threshold,
            params.mapq_threshold
        )
        //aggregate per tract
        get_per_tract_stats(
            sort_bed.out.sorted_bed,
            add_tract_labels.out.labelled_pileup
        )
        //tract thresholds different from per base?
//         filter_low_scoring_tracts(
//             get_per_tract_stats.out.per_tract,
//             params.coverage_threshold,
//             params.baseq_threshold,
//             params.mapq_threshold
//         )




        """
    coverage_threshold = 25 // minimum acceptable value for coverage per base
    normalize_to_mean_coverage = null // If set, coverage will be normalized to match the provided mean
    mapq_threshold = 30 // minimum acceptable first quartile (Q1) of the MAPQ scores of mapped reads per base
    baseq_threshold = 30 // minimum acceptable first quartile (Q1) of the BASEQ scores of mapped reads per base

        """
}