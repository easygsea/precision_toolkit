include {
    ADD_TARGET_LABELS
    GET_PER_TARGET_AGGREGATED_STATS
    GENERATE_PER_BASE_SUMMARY
    SCORE_OUTPUT as SCORE_BASES_PER_LIBRARY
    SCORE_OUTPUT as SCORE_TARGETS_PER_LIBRARY
    SCORE_OUTPUT as SCORE_PER_BASE_SUMMARY
    GENERATE_VISUALIZATION
} from '../../modules/target_evaluation/main'

include {
    INDEX_BAM_FILE as INDEX_BAM_FILES
    GET_PER_BASE_STATS
    GET_PER_BASE_STATS_NO_PARSE
} from '../../modules/bam/main'

include { SUBSET_CRAM_TO_BAM    } from '../../modules/cram/main'
include { SORT_BED              } from '../../modules/bed/main'

// collect all scoring thresholds
def scoring_thresholds = tuple (
    params.coverage_threshold,
    params.baseq_threshold,
    params.mapq_threshold
)

// Main variant gene target evaluation workflow
workflow gene_target_evaluation_workflow {
    main:
    // 0. Setup
    targets_bed = SORT_BED(file(params.targets_bed)).sorted_bed

    // build input channel & branch based on filetype
    mixed_aligned_ch = channel
        .fromPath(params.aligned_files)
        .map{file_path ->
            def sample_name = file_path.getName().replaceFirst(/\..*$/, "")
            def matcher = file_path.toString() =~ /IX\d{5}/
            def pool_id = matcher.find() ? matcher.group(0) : null
            tuple (sample_name, file_path, pool_id)
        }
        .branch { sample_name, file_path, pool_id ->
            def ext = file_path.extension.toLowerCase()
            bam: ext == 'bam'
            cram: ext == 'cram'
            other: true
        }

    // if no genome_ref, skip any cram file & output warning for each file not processed
    if (!params.genome_ref) {
       mixed_aligned_ch.cram
            .view {sample_name, no_ref_cram, pool_id ->
                log.warn "No genome reference provided for cram files. \n" +
                "SKIPPING ${no_ref_cram}" }
       bam_ch = mixed_aligned_ch.bam
    }
    // else, do conversion for any cram files
    else {
        bam_ch = mixed_aligned_ch.bam
            .concat(
                CRAM_TO_BAM_WITH_SUBSET (
                    mixed_aligned_ch.cram,
                    file(params.genome_ref),
                    targets_bed,
                    32
                )
            )
    }

    // TODO: erase print line
    bam_ch.view{"FINAL BAMS CHANNEL: $it"}

    INDEX_BAM_FILES(bam_ch)

    // 1. Get per-base stats
    GET_PER_BASE_STATS(
        targets_bed,
        bam_ch,
        params.mpileup_baseq_min,
        params.mpileup_mapq_min
    )
    ADD_TARGET_LABELS(
        targets_bed,
        GET_PER_BASE_STATS.out.parsed_pileup
    )

    // 1.5 aside to output raw mpileup if needed
    if (params.output_raw_mpileup) {
        GET_PER_BASE_STATS_NO_PARSE(
            targets_bed,
            bam_ch,
            params.mpileup_baseq_min,
            params.mpileup_mapq_min
        )
    }

    // 2. Aggregate per target (q1s)
    GET_PER_TARGET_AGGREGATED_STATS(
        targets_bed,
        ADD_TARGET_LABELS.out.labelled_pileup
    )

    // 3. Aggregate per base across libraries
    GENERATE_PER_BASE_SUMMARY (
        ADD_TARGET_LABELS.out.labelled_pileup
            .collectFile(name: "combined_labelled_pileups.txt"){it[1]}
    )

    // 4. Score files on thresholds
    SCORE_BASES_PER_LIBRARY (
        ADD_TARGET_LABELS.out.labelled_pileup,
        scoring_thresholds
    )
    SCORE_TARGETS_PER_LIBRARY (
        GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated,
        scoring_thresholds
    )

    // TODO: Does it make sens to score the per_base_summary?
    SCORE_PER_BASE_SUMMARY (
        GENERATE_PER_BASE_SUMMARY.out.all_libraries_per_base,
        scoring_thresholds
    )

    // 5. Generate visualization per target
    if (params.visualize) {
        GENERATE_VISUALIZATION (
            GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated.collect{it[1]},
            GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated.collect{it[2]},
            "plot",
            scoring_thresholds
        )
    }

//     TODO: normalize_to_mean_coverage = null // If set, coverage will be normalized to match the provided mean

}
