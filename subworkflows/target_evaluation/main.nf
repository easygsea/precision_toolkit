include {
    NORMALIZE_COVERAGE_TO_TARGET
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


    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Handle workflow input & file formats
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */

    // make sure bed is sorted
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
                SUBSET_CRAM_TO_BAM (
                    mixed_aligned_ch.cram,
                    file(params.genome_ref),
                    targets_bed,
                    32
                )
            )
    }

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Process BAM files to extract metrics
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    INDEX_BAM_FILES(bam_ch)

    // Stage 1: Get per-base stats (Raw Coverage, Q1 of each base MapQ BaseQ)
    GET_PER_BASE_STATS(
        targets_bed,
        bam_ch,
        params.min_bq_per_read,
        params.min_mq_per_read
    )
    ADD_TARGET_LABELS(
        targets_bed,
        GET_PER_BASE_STATS.out.parsed_pileup
    )

    // normalize if target coverage provided
    if (!params.normalize_coverage) {
        sample_stage_output = ADD_TARGET_LABELS.out.labelled_pileup
    } else {
        NORMALIZE_COVERAGE_TO_TARGET(
            targets_bed,
            ADD_TARGET_LABELS.out.labelled_pileup,
            params.normalize_coverage,
        )
        sample_stage_output = NORMALIZE_COVERAGE_TO_TARGET.out.normalized_pileup
    }

    // aside: output raw mpileup if needed
    if (params.output_raw_mpileup) {
        GET_PER_BASE_STATS_NO_PARSE(
            targets_bed,
            bam_ch
        )
    }

    // Stage 2:  Aggregate per target (Q1 of per-base stats)
    GET_PER_TARGET_AGGREGATED_STATS(
        targets_bed,
        sample_stage_output
    )

    // Stage 3: Aggregate per base across libraries (Median of per-base stats)
    GENERATE_PER_BASE_SUMMARY (
        sample_stage_output.collectFile(name: "combined_labelled_pileups.txt"){it[1]}
    )

    // Stage 4: Score files on thresholds
    SCORE_BASES_PER_LIBRARY (
        sample_stage_output,
        scoring_thresholds
    )
    SCORE_TARGETS_PER_LIBRARY (
        GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated,
        scoring_thresholds
    )
    SCORE_PER_BASE_SUMMARY (
        GENERATE_PER_BASE_SUMMARY.out.all_libraries_per_base,
        scoring_thresholds
    )

    // Stage 5: Generate visualization per target
    if (params.visualize) {
        GENERATE_VISUALIZATION (
            GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated.collect{it[1]},
            GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated.collect{it[2]},
            "plot",
            scoring_thresholds
        )
    }
}
