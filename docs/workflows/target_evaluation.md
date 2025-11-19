# Target Evaluation

The target evaluation workflow extracts coverage and computes the first-quartile base quality (BASEQ) and
mapping quality (MAPQ) for every base in your target regions using the provided alignment data (in CRAM or BAM format).
Each base is marked as pass/fail based on satisfying minimum thresholds for each metric.

Library-level, per-base metrics (as described above) are evaluated for each library and informs library-specific problem bases.
Further aggregation and analysis on two rules additionally provide reliable performance estimates on different levels: <br>
- A) Library-level, per-target: high percentage of bases failed in each target region informs library-specific, target-level issues. <br>
- B) Cohort-level, per-base: high percentage of libraries that fail on the same bases informs system-level issue across the pipeline. <br>

>For more details about scoring and analysis, see [Target Evaluation Scoring Explained](#target-evaluation-scoring-explained).

Tracts summarizing low-performance regions across all libraries identified in (B) are also provided to assist with analysis and reporting.

Lastly, a host of metrics for fine-tuning analysis metrics and threshold are provided in [Target Evaluation Parameters](#target-evaluation-parameters) for high-precision and customizable analysis your data.
Additional options like `--visualize` and `--normalize_coverage` are provided to facilitate comparison and reporting across libraries.


## Quick Start

Run the following command to input a mix of CRAM and BAM alignment files. Symlinks are accepted.

*Important to provide a genome reference if inputting CRAM files.*
```bash
nextflow run main.nf \
--workflows target_evaluation \
--aligned_files '<path/to/alignment_files_dir/*.{cram,bam}>' \
--genome_ref <path/to/genome_ref> \
--targets_bed <path/to/targets_bed> \
--output_dir <path/to/output_dir> \
--visualize
```

Custom pass/fail scoring by setting three threshold parameters: coverage, BASEQ, and MAPQ.
```bash
nextflow run main.nf \
--workflows target_evaluation \
--aligned_files '<path/to/alignment_files_dir/*.bam>' \
--targets_bed <path/to/targets_bed> \
--output_dir <path/to/output_dir> \
--coverage_threshold <min_coverage> \
--baseq_threshold <min_baseq> \
--mapq_threshold <min_mapq>
```


## Target Evaluation Manual

- [Target Evaluation Parameters](#target-evaluation-parameters)
- [Target Evaluation Output](#target-evaluation-output)
- [Target Evaluation Scoring Explained](#target-evaluation-scoring-explained)


### Target Evaluation Parameters

**Required Parameters:**
- `--aligned_files`: Glob including BAM and/or CRAM files to be processed (eg. '/path/to/dir/*'). Any other filetypes ignored. If CRAM files included, also provide `--genome_ref`.
- `--targets_bed`: Target regions in BED format.
- `--genome_ref`: Reference genome FASTA file. Required to process any input CRAM files.

**Optional Parameters:**
- `--target_evaluation_subdir`: Subdirectory for target evaluation results (default: target_evaluation)
- `--output_raw_mpileup`: Flag to output raw mpileup file.
- `--normalize_coverage`: If set, coverage across the targets bed for every sample is normalized and scaled to center on this value. This function is provided to improve comparability and adjust for variations in sequencing depth cross samples if needed.
- `--visualize`: Flag to generate per-target level plots for each stat.

**Fine-Tuning Parameters**
- `--coverage_threshold`: Minimum coverage threshold for pass (default = 25).
- `--baseq_threshold`: Minimum BASEQ threshold for pass, scored on first quartile of all reads per base (default = 30).
- `--mapq_threshold`: Minimum MAPQ score threshold for pass, scored on first quartile of all reads per base (default = 30).
- `--target_fail_tolerance`: Maximum tolerable percentage of bases failed for target-level PASS per sample (default = 0.25, non-inclusive).
- `--base_fail_tolerance`: Maximum tolerable percentage of libraries failing at a base for base-level PASS across all libraries (default = 0.25, non-inclusive).
- `--tract_gap_tolerance`: Maximum gap tolerance between fail regions when building tracts (default = 2).

**Custom Metric Parameters** (optional parameters to fine-tune filtering of raw mpileup output for each metric):
- `--min_bq_per_read.coverage_analysis`: Minimum BASEQ for read to be included in coverage count at each position (default = 10).
- `--min_bq_per_read.mapq_analysis`: Minimum BASEQ for read to be included in MAPQ Q1 analysis at each position (default = 10).
- `--min_bq_per_read.baseq_analysis`: Minimum BASEQ for read to be included in BASEQ Q1 analysis at each position (default = 0).
- `--min_mq_per_read.coverage_analysis`: Minimum MAPQ for read to be included in coverage count at each position (default = 1).
- `--min_mq_per_read.mapq_analysis`: Minimum MAPQ for read to be included in MAPQ Q1 analysis at each position (default = 0).
- `--min_mq_per_read.baseq_analysis`: Minimum MAPQ for read to be included in BASEQ Q1 analysis at each position (default = 1).

### Target Evaluation Output

**Directory Structure:**

For example, when `--output_raw_mpileup` and `--visualize` is flagged:
```bash
<output_dir>
└── <target_evaluation_subdir>
    ├── all_libraries_per_base_metrics.scored.txt
    ├── library_level   # Library specific per-base and per-target outputs
    │   ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.per_base.parsed.labelled.scored.txt
    │   ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt
    │   ├── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.per_base.parsed.labelled.scored.txt
    │   └── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt
    ├── plots           # Per-target plots (if '--visualize' enabled)
    │   ├── plot_CENTILE25(BQ_Q1).png
    │   ├── plot_CENTILE25(COV).png
    │   └── plot_CENTILE25(MQ_Q1).png
    ├── raw_mpileups    # Raw mpileup output per-library (if '--output_raw_mpilups' enabled)
    │   ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.raw.txt
    │   └── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.raw.txt
    └── tracts          # Tracts build from analysis of all libraries at each base
        ├── tracts.bq_score.bed
        ├── tracts.cov_score.bed
        ├── tracts.mq_score.bed
        └── tracts.unionized.bed
```

**Example Output:**

*NOTE: Output files are 1-indexed. If no bases pass the minimum metric parameters, then Q1 will be reported as -1 (no valid reads for this parameter).*

1. Per-base output
```bash
#CHROM	POS	TRACT	POOL	COVERAGE	BASEQ_Q1	MAPQ_Q1	SCORE
chr5	664	MSH3_NM_002439_EXON01_2	IX00001	1	40	60	FAIL
chr5	665	MSH3_NM_002439_EXON01_2	IX00001	1	-1	60	FAIL
```
2. Per-target output
```bash
#CHROM	POS	TRACT	POOL	CENTILE25(COV)	CENTILE25(BQ_Q1)	CENTILE25(MQ_Q1)	LEN	NUM_BASES_FAIL	PCT_BASES_FAIL	SCORE
chr5	NA	MSH3_NM_002439_EXON01_2	IX00001	0	-1	-1	61	61	100	FAIL
```
3. Per-base aggregated across libraries
```bash
#CHROM	POS	TRACT	POOL	CENTILE25(COV)	CENTILE25(BQ_Q1)	CENTILE25(MQ_Q1)	NUM_LIB_FAIL(COV)	NUM_LIB_FAIL(BQ)	NUM_LIB_FAIL(MQ)	PCT_LIB_FAIL(COV)	PCT_LIB_FAIL(BQ)	PCT_LIB_FAIL(MQ)	COV_SCORE	BQ_SCORE	MQ_SCORE
chr5	664	MSH3_NM_002439_EXON01_2	AGGREGATE	0	-1	-1	2	1	1	100	50	50	FAIL	FAIL	FAIL
chr5	665	MSH3_NM_002439_EXON01_2	AGGREGATE	0	-1	-1	2	1	1	100	50	50	FAIL	FAIL	FAIL
```
4. Tracts bed
```bash
#chrom	start	end	name	mean_fail_centile_score
chr5	664	675	MSH3_NM_002439_EXON01_2	1.78
chr5	682	725	MSH3_NM_002439_EXON01_2	5.58
```


### Target Evaluation Scoring Explained
Scoring is conducted based on the following metrics for each file

#### A) Library-level, per-base
   - COVERAGE: Each base has a coverage count of all aligned reads covering the base that fulfill the coverage analysis requirements.
   - BASEQ_Q1: Calculated as the first quartile of all BASEQ scores at each loci, of reads that fulfill the BASEQ analysis requirements.
   - MAPQ_Q1: Calculated as the first quartile of all MAPQ score at each loci of reads that fulfill the MAPQ analysis requirements.

_Overall, a `FAIL` here tells us that this base has a problem in this library. For details about analysis fine-tuning and metrica analysis requirements, see [custom metric parameters](#target-evaluation-parameters)._

#### B) Library-level, per-target
   - PCT_BASES_FAIL: Each target per libary passes only of the percent of bases failing within the target's region is less than `--target_fail_tolerance`.

_Overall, a `FAIL` here suggests that there is a problem with this target in this library. Specifically, 25% or more (default) of the bases within this target-region failed on one or more of the 3 metrics._

#### C) Cohort-level, per-base

On a Cohort-level, we evaluate systemic issues based on the percentage of libraries failed on each metric. The threshold for percentage of libraries failed can be fine-tuned with `--base_fail_tolerance`.
   - PCT_LIB_FAIL(COV): Calculated as the percent of libraries that failed on coverage on this base (as defined in section A). Scoring for this metric is recorded under the COV_SCORE heading.
   - PCT_LIB_FAIL(BQ): Calculated as the percent of libraries that failed on base quality on this base (as defined in section A). Scoring for this metric is recorded under the BQ_SCORE heading.
   - PCT_LIB_FAIL(MQ): Calculated as the percent of libraries that failed on mapping quality on this base (as defined in section A). Scoring for this metric is recorded under the MQ_SCORE heading.

_Overall, a `FAIL` here suggests that there is a problem with this base systemically, causing 25% or more (default) of all libraries evaluated to fail on this base (with metric-specific breakdown).
This suggests a more generalized technical or biological problem (eg. issues inherent to the genome itself, NGS limitations, or lab/instrument processing)._

Note: the scoring here is used to build tracts that identify failing regions with some gap tolerance as defined by `--tract_gap_tolerance`.

#### D) Cohort-level, per-target (in-development)
