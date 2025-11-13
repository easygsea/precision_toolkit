include {
    NORMALIZE_COVERAGE_TO_TARGET
    ADD_TARGET_LABELS
    GET_PER_TARGET_AGGREGATED_STATS
    GENERATE_PER_BASE_SUMMARY
    SCORE_OUTPUT_ON_METRICS as SCORE_BASES_PER_LIBRARY
    SCORE_OUTPUT_ON_FIELD as SCORE_TARGETS_PER_LIBRARY
    SCORE_OUTPUT_ON_FIELD as SCORE_PER_BASE_SUMMARY_ON_COV
    SCORE_OUTPUT_ON_FIELD as SCORE_PER_BASE_SUMMARY_ON_BQ
    SCORE_OUTPUT_ON_FIELD as SCORE_PER_BASE_SUMMARY_ON_MQ
    GENERATE_TRACTS
    GENERATE_VISUALIZATION
} from '../../modules/target_evaluation/main'

include {
    INDEX_BAM_FILE as INDEX_BAM_FILES
    GET_PER_BASE_STATS
    GET_PER_BASE_STATS_NO_PARSE
} from '../../modules/bam/main'

include { SUBSET_CRAM_TO_BAM    } from '../../modules/cram/main'
include { SORT_BED              } from '../../modules/bed/main'


// Main variant gene target evaluation workflow
workflow gene_target_evaluation_workflow {
    main:

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Handle workflow setup, input & file formats
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */

    // define workflow variables
    def metrics_scoring_thresholds = tuple (
        params.coverage_threshold,
        params.baseq_threshold,
        params.mapq_threshold
    )
    def scoring_params = [
        tuple ("SCORE", "PCT_BASES_FAIL", params.target_fail_tolerance),
        tuple ("COV_SCORE", "PCT_LIB_FAIL(COV)", params.base_fail_tolerance),
        tuple ("BQ_SCORE", "PCT_LIB_FAIL(BQ)", params.base_fail_tolerance),
        tuple ("MQ_SCORE", "PCT_LIB_FAIL(MQ)", params.base_fail_tolerance)
    ]
    def tract_params = channel.of ("COV_SCORE", "BQ_SCORE", "MQ_SCORE")

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

    // STAGE 1: Get per-base stats (Raw Coverage, Q1 of each base MapQ BaseQ)
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
    if (!params.normalize_to_target_coverage) {
        sample_stage_output = ADD_TARGET_LABELS.out.labelled_pileup
    } else {
        NORMALIZE_COVERAGE_TO_TARGET(
            targets_bed,
            ADD_TARGET_LABELS.out.labelled_pileup,
            params.normalize_to_target_coverage,
        )
        sample_stage_output = NORMALIZE_COVERAGE_TO_TARGET.out.normalized_pileup
    }

    // score based on metrics thresholds
    SCORE_BASES_PER_LIBRARY (
        sample_stage_output,
        metrics_scoring_thresholds
    )

    // aside: output raw mpileup if needed (troubleshooting option)
    if (params.output_raw_mpileup) {
        GET_PER_BASE_STATS_NO_PARSE(
            targets_bed,
            bam_ch
        )
    }

    // STAGE 2: Aggregate per target (percentile of per-base stats)
    GET_PER_TARGET_AGGREGATED_STATS(
        targets_bed,
        SCORE_BASES_PER_LIBRARY.out.scored_output,
        params.target_fail_tolerance //percentile - >= X% of bases are above this value
    )

    // score based on PCT_FAIL/TARGET
    SCORE_TARGETS_PER_LIBRARY (GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated, scoring_params[0])

    // STAGE 3: Aggregate per base across libraries (percentile of per-base stats)
    GENERATE_PER_BASE_SUMMARY (
        SCORE_BASES_PER_LIBRARY.out.scored_output.collectFile(name: "combined_labelled_pileups.txt"){it[1]},
        metrics_scoring_thresholds, //detailed output: num libraries failed/metric
        params.base_fail_tolerance //percentile - >= X% of libraries above this value
        //TODO: should display percentile be separate from threshold/tolerance percentile?
    )

    // score each base on how many libraries passed for each metric
    SCORE_PER_BASE_SUMMARY_ON_COV (GENERATE_PER_BASE_SUMMARY.out.all_libraries_per_base, scoring_params[1])
    SCORE_PER_BASE_SUMMARY_ON_BQ (SCORE_PER_BASE_SUMMARY_ON_COV.out.scored_output, scoring_params[2])
    SCORE_PER_BASE_SUMMARY_ON_MQ (SCORE_PER_BASE_SUMMARY_ON_BQ.out.scored_output, scoring_params[3])

    //SCORE_PER_BASE_SUMMARY_ON_MQ.out.scored_output --> generate tracts
    GENERATE_TRACTS (
        SCORE_PER_BASE_SUMMARY_ON_MQ.out.scored_output,
        tract_params,
        params.tract_gap_tolerance
    )

    // Stage 5: Generate visualization per target
    if (params.visualize) {
        GENERATE_VISUALIZATION (
            GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated.collect{it[1]},
            GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated.collect{it[2]},
            "plot",
            metrics_scoring_thresholds
        )
    }
}
