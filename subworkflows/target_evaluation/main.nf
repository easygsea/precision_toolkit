include {
    add_target_labels
    get_per_target_aggregated_stats
    generate_per_base_summary
    score_output as score_bases_per_library
    score_output as score_targets_per_library
    score_output as score_per_base_summary
    generate_visualization
} from '../../modules/target_evaluation/main'

include { get_per_base_stats } from '../../modules/target_evaluation/mpileup'
include { index_bam_file as index_bam_files } from '../../modules/bam/main'
include { sort_bed } from '../../modules/bed/main'

//bedmap tool (not currently being developed)
include {
    build_per_base_bed
    convert_bam_to_bed
    get_per_base_depth
    get_per_base_stats_with_bedmap as extract_per_base_mapq_with_bedmap
    get_per_base_stats_with_bedmap as extract_per_base_baseq_with_bedmap
    convert_to_baseq_scores
} from '../../modules/target_evaluation/bedmap'
include { SORT_BED                          } from '../../modules/bed/main'


// TODO: valid input checks function
// def verify_input() {
//     if (!file("${params.targets_bed}").exists()) error "Target bed not found: ${params.targets_bed}"
//     if (!file(params.bams_dir).exists()) error "Bams dir not found: ${params.bams_dir}"
// }

// Main variant gene target evaluation workflow
workflow gene_target_evaluation_workflow {
    main:

    //build channel with bam files (requires input regex 'path/to/bams/dir/*.bam*')
    bam_ch = channel
        .fromPath(params.bams_dir)
        .map{file_path ->
            def matcher = file_path.toString() =~ /IX\d{5}/
            def pool_id = matcher.find() ? matcher.group(0) : null
            tuple (file_path, pool_id)
        }

    // TODO: del
    //bam_ch.view{item -> "BAMS_CH: $item"}
    println "TARGETS BED: ${params.targets_bed}"

    // 0. Setup
    sort_bed(file(params.targets_bed))
    index_bam_files(bam_ch)


    // 1. Get per-base stats mpileup on stats
    get_per_base_stats(
        SORT_BED.out.sorted_bed,
        bam_ch,
        params.mpileup_baseq_min,
        params.mpileup_mapq_min
    )
    add_target_labels(
        SORT_BED.out.sorted_bed,
        get_per_base_stats.out.parsed_pileup
    )

    // 1.5 aside
    if (params.output_raw_mpileup) {
        get_per_base_stats(
            SORT_BED.out.sorted_bed,
            bam_ch,
            params.mpileup_baseq_min,
            params.mpileup_mapq_min
        )
    }

    // 2. Aggregate per target (q1s)
    get_per_target_aggregated_stats(
        SORT_BED.out.sorted_bed,
        add_target_labels.out.labelled_pileup
    )

    // 3. Aggregate per base across libraries
    generate_per_base_summary (
        add_target_labels.out.labelled_pileup
            .collectFile(name: "combined_labelled_pileups.txt"){it[0]}
    )

    // 4. Score files on thresholds
    score_bases_per_library (
        add_target_labels.out.labelled_pileup.map{it[0]},
        params.coverage_threshold,
        params.baseq_threshold,
        params.mapq_threshold
    )
    score_targets_per_library (
        get_per_target_aggregated_stats.out.per_target_aggregated.map{it[0]},
        params.coverage_threshold,
        params.baseq_threshold,
        params.mapq_threshold
    )
    // TODO: Does it make sens to score this?
    score_per_base_summary (
        generate_per_base_summary.out.all_libraries_per_base,
        params.coverage_threshold,
        params.baseq_threshold,
        params.mapq_threshold
    )

    // 5. Generate visualization per target
    if (params.visualize) {
        generate_visualization (
            get_per_target_aggregated_stats.out.per_target_aggregated.collect{it[0]},
            get_per_target_aggregated_stats.out.per_target_aggregated.collect{it[1]},
            "target_eval_visual",
            params.coverage_threshold,
            params.baseq_threshold,
            params.mapq_threshold
        )
    }

    // TODO: normalize_to_mean_coverage = null // If set, coverage will be normalized to match the provided mean

}