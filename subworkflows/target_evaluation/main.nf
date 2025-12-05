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
    UNIONIZE_TRACTS
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
    def metrics_thresholds_and_headings = [
        cov: [
            library_header: "COVERAGE_P${params.read_fail_tolerance*100 as int}",
            target_header: "TARGET_P${params.target_fail_tolerance*100 as int}(BASE_COV)",
            base_header: "SAMPLES_P${params.base_fail_tolerance*100 as int}(BASE_COV)",
            base_score_header: "PCT_LIB_FAIL(COV)",
            base_score_output_header: "COV_SCORE",
            threshold: params.coverage_threshold
        ],
        bq: [
            library_header: "BASEQ_P${params.read_fail_tolerance*100 as int}",
            target_header: "TARGET_P${params.target_fail_tolerance*100 as int}(BASE_BQ_P${params.read_fail_tolerance*100 as int})",
            base_header: "SAMPLES_P${params.base_fail_tolerance*100 as int}(BASE_BQ_Q${params.read_fail_tolerance*100 as int})",
            base_score_header: "PCT_LIB_FAIL(BQ)",
            base_score_output_header: "BQ_SCORE",
            threshold: params.baseq_threshold
        ],
        mq: [
            library_header: "MAPQ_P${params.read_fail_tolerance*100 as int}",
            target_header: "TARGET_P${params.target_fail_tolerance*100 as int}(BASE_MQ_P${params.read_fail_tolerance*100 as int})",
            base_header: "SAMPLES_P${params.base_fail_tolerance*100 as int}(BASE_MQ_P${params.read_fail_tolerance*100 as int})",
            base_score_header: "PCT_LIB_FAIL(MQ)",
            base_score_output_header: "MQ_SCORE",
            threshold: params.mapq_threshold
        ],
        gen: [
            target_score_header: "PCT_BASES_FAIL",
            target_score_output_header: "SCORE"
        ]
    ]

    // make sure bed is sorted
    targets_bed = SORT_BED(file(params.targets_bed)).sorted_bed

    // build input channel & branch based on filetype
    mixed_aligned_ch = Channel
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
    INDEX_BAM_FILES (bam_ch)

    // STAGE 1: Get per-base stats (Raw Coverage, Q1 of each base MapQ BaseQ)
    GET_PER_BASE_STATS (
        targets_bed,
        bam_ch,
        params.min_bq_per_read,
        params.min_mq_per_read,
        params.read_fail_tolerance
    )
    ADD_TARGET_LABELS (
        GET_PER_BASE_STATS.out.parsed_pileup,
        targets_bed,
        metrics_thresholds_and_headings
    )

    // normalize if target coverage provided
    if (!params.normalize_coverage) {
        sample_stage_output = ADD_TARGET_LABELS.out.labelled_pileup
    } else {
        NORMALIZE_COVERAGE_TO_TARGET (
            ADD_TARGET_LABELS.out.labelled_pileup,
            targets_bed,
            params.normalize_coverage
        )
        sample_stage_output = NORMALIZE_COVERAGE_TO_TARGET.out.normalized_pileup
    }

    // score based on metrics thresholds
    SCORE_BASES_PER_LIBRARY (
        sample_stage_output,
        metrics_thresholds_and_headings
    )

    // aside: output raw mpileup if needed (troubleshooting option)
    if (params.output_raw_mpileup) {
        GET_PER_BASE_STATS_NO_PARSE (
            targets_bed,
            bam_ch
        )
    }

    // STAGE 2: Aggregate per target (percentile of per-base stats)
    GET_PER_TARGET_AGGREGATED_STATS (
        SCORE_BASES_PER_LIBRARY.out.scored_output,
        targets_bed,
        params.target_fail_tolerance,
        metrics_thresholds_and_headings
    )

    // score based on PCT_FAIL/TARGET
    SCORE_TARGETS_PER_LIBRARY (
        GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated,
        metrics_thresholds_and_headings.gen.target_score_header,
        metrics_thresholds_and_headings.gen.target_score_output_header,
        params.target_fail_tolerance
        //TODO: should display percentile be separate from threshold/tolerance percentile?
    )

    // STAGE 3: Aggregate per base across libraries (percentile of per-base stats)
    GENERATE_PER_BASE_SUMMARY (
        SCORE_BASES_PER_LIBRARY.out.scored_output.collectFile(name: 'combined_labelled_pileups.txt'){it[1]},
        params.base_fail_tolerance,
        metrics_thresholds_and_headings //for detailed output: num libraries failed/metric
        //TODO: should display percentile be separate from threshold/tolerance percentile?
    )

    // score each base on how many libraries passed for each metric
    SCORE_PER_BASE_SUMMARY_ON_COV (
        GENERATE_PER_BASE_SUMMARY.out.all_libraries_per_base,
        metrics_thresholds_and_headings.cov.base_score_header,
        metrics_thresholds_and_headings.cov.base_score_output_header,
        params.base_fail_tolerance
     )
    SCORE_PER_BASE_SUMMARY_ON_BQ (
        SCORE_PER_BASE_SUMMARY_ON_COV.out.scored_output,
        metrics_thresholds_and_headings.bq.base_score_header,
        metrics_thresholds_and_headings.bq.base_score_output_header,
        params.base_fail_tolerance
    )
    SCORE_PER_BASE_SUMMARY_ON_MQ (
        SCORE_PER_BASE_SUMMARY_ON_BQ.out.scored_output,
        metrics_thresholds_and_headings.mq.base_score_header,
        metrics_thresholds_and_headings.mq.base_score_output_header,
        params.base_fail_tolerance
    )

    // generate tracts per metric
    GENERATE_TRACTS (
        SCORE_PER_BASE_SUMMARY_ON_MQ.out.scored_output,
        Channel.from(
            metrics_thresholds_and_headings
                .findAll { k, v -> ['cov','bq','mq'].contains(k) }
                .values() ),
        params.tract_gap_tolerance
    )
    // generate unionized tract
    UNIONIZE_TRACTS (GENERATE_TRACTS.out.tract_bed.collectFile(name: 'combined.bed', skip: 1))

    // Stage 5: Generate visualization per target
    if (params.visualize) {
        GENERATE_VISUALIZATION (
            GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated.collect{it[1]},
            GET_PER_TARGET_AGGREGATED_STATS.out.per_target_aggregated.collect{it[2]},
            "plot",
            metrics_thresholds_and_headings
                .findAll { k, v -> ['cov','bq','mq'].contains(k) }
                .collectEntries {  k,v -> [ (v.target_header): v.threshold ] }
        )
    }
}
