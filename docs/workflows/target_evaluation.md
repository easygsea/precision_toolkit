# Target Evaluation

The target evaluation workflow extracts coverage and computes the first-quartile base
quality (BASEQ) and mapping quality (MAPQ) for every base in your target regions using
your alignment data (in CRAM or BAM format).
Each base is marked as pass/fail based on satisfying minimum thresholds for each
metric. You may adjust these thresholds to fine tune the evaluation for your data.
In further detail, the specific minimum parameters per base per read to be considered
for each metric can also be adjusted to assist analysis
(see [custom metric parameters](#target-evaluation-parameters)).

Per-base metrics are further aggregated on two rules to provide reliable performance estimates: <br>
- A) Per target region within each library/sample, using the first-quartile (Q1) value. <br>
- B) Per base across all libraries/samples, using the median value. <br>

Visualization on per-target level optionally enabled by `--visualize` option.

Coverage can be scaled to center on a specific target value with `--normalize_coverage`
to improve comparability across samples and mirror expected sequencing depth.

See [Target Evaluation Parameters](#target-evaluation-parameters) for details.


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
- `--workflows target_evaluation`: Required parameter to run target evaluation workflow.
- `--aligned_files`: Glob including BAM and/or CRAM files to be processed (eg. '/path/to/dir/*'). Any other filetypes ignored. If CRAM files included, also provide `--genome_ref`.
- `--targets_bed`: Target regions in BED format.
- `--genome_ref`: Reference genome FASTA file. Required to process any input CRAM files.

**Optional Parameters:**
- `--normalize_coverage`: If set, coverage across the targets bed for every sample is normalized and scaled to center on this value.
- `--coverage_threshold`: Minimum coverage threshold for pass (default = 25).
- `--baseq_threshold`: Minimum BASEQ threshold for pass, scored on first quartile of all reads per base (default = 30).
- `--mapq_threshold`: Minimum MAPQ score threshold for pass, scored on first quartile of all reads per base (default = 30).
- `--visualize`: Flag to generate per-target level plots for each stat.
- `--output_raw_mpileup`: Flag to output raw mpileup file.

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
└── target_eval_results
    ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.per_base.parsed.labelled.scored.txt                     # Per-base output
    ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt   # Per-target output
    ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.raw.txt                                                 # Raw mpilup output
    ├── plot_BASEQ_Q1_Q1.png                # Per-target plot BASEQ
    ├── plot_COVERAGE_Q1.png                # Per-target plot coverage
    ├── plot_MAPQ_Q1_Q1.png                 # Per-target plot MAPQ
    ├── summary_per_base_median.scored.txt  # Per-base aggregated across libraries
    ├── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.per_base.parsed.labelled.scored.txt                    # Per-base output
    ├── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt  # Per-target output
    └── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.raw.txt                                                # Raw mpilup output
```

**Example Output:**

*NOTE: Output files are 1-indexed. If no bases pass the minimum metric parameters, then Q1 will be reported as -1.*

1. Per-base output
```bash
#CHROM	POS	TRACT	POOL	COVERAGE	BASEQ_Q1	MAPQ_Q1	SCORE
chr5	664	MSH3_NM_002439_EXON01_2	IX00001	1	40	60	FAIL
chr5	665	MSH3_NM_002439_EXON01_2	IX00001	1	-1	60	FAIL
...
```
2. Per-target output
```bash
#CHROM	POS	TRACT	POOL	COVERAGE_Q1	BASEQ_Q1_MED	BASEQ_Q1_Q1	MAPQ_Q1_MED	MAPQ_Q1_Q1	SCORE
chr5	NA	MSH3_NM_002439_EXON02_2	IX00001	1	40	60	FAIL
```
3. Per-base aggregated across libraries
```bash
#CHROM	POS	TRACT	POOL	COVERAGE_MED	BASEQ_MED_Q1	MAPQ_MED_Q1	SCORE
chr5	664	MSH3_NM_002439_EXON01_2	AGGREGATE	0.5	20	30		FAIL
chr5	665	MSH3_NM_002439_EXON01_2	AGGREGATE	0.5	20	30		FAIL
...
```


### Target Evaluation Scoring Explained
Scoring is conducted based on the following metrics for each file

1. Per-base
   - COVERAGE: Each base has a coverage count of all aligned reads covering the base
   that fulfill the coverage analysis requirements.
   - BASEQ_Q1: Calculated as the first quartile of all BASEQ scores at each loci, of
   reads that fulfill the BASEQ analysis requirements.
   - MAPQ_Q1: Calculated as the first quartile of all MAPQ score at each loci of
   reads that fulfill the MAPQ analysis requirements.

   For details about analysis requirements, see [custom metric parameters](#target-evaluation-parameters).


2. Per-target
   - COVERAGE_Q1: First quartile of the coverages of all bases within the target region.
   - BASEQ_Q1_Q1: First quartile of all BASEQ_Q1s of all bases within the target region.
   - MAPQ_Q1_Q1: First quartile of all MAPQ_Q1s of all bases within the target region.

   Overall, a `FAIL` here suggests that more than 75% of the bases within this target-region failed on one or more of the 3 metrics.


3. Per-base aggregated across libraries
   - COVERAGE_MED: Median coverage of this loci across all libraries.
   - BASEQ_MED_Q1: Median BASEQ_Q1s of this loci across all libraries.
   - MAPQ_MED_Q1: Median MAPQ_Q1s of this loci across all libraries.
