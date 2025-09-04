# Target Evaluation

The target evaluation workflow extracts the coverage, and first quartile baseQ and mapQ for each base in the provided target space.
Following extraction, each base is scored as pass/fail based on thresholds for each metric (user provided or default).
Per-base metrics are further aggregated on two rules: A) per-target per-library (method: Q1) and B) per-base across libraries (method: median) to provide better performance estimates.
Visualization on per-target level optionally enabled by `--visualize` option.


## Quick Start

Run the following command to input a mix of cram and bam files. Symlinks are accepted.

*Important to provide a genome reference if inputting cram files.*
```bash
nextflow run main.nf \
--workflows target_evaluation \
--aligned_files <path/to/alignment_files_dir/*.{cram,bam}> \
--genome_ref <path/to/genome_ref> \
--targets_bed <path/to/targets_bed> \
--output_dir <path/to/output_dir> \
--visualize
```

Customize pass/fail scoring with 3 "threshold" options.
```bash
nextflow run main.nf \
--workflows target_evaluation \
--aligned_files <path/to/alignment_files_dir/*.bam> \
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
- `--aligned_files`: Glob including bam and/or cram files to be processed (eg. '/path/to/dir/*'). Any other filetypes ignored. If cram files included, also provide `--genome_ref`.
- `--targets_bed`: Target space for per-base metric extraction.
- `--genome_ref`: Reference genome FASTA file. Required to process any input cram files.

**Optional Parameters:**
- `--coverage_threshold`: Minimum coverage threshold for pass (default = 25).
- `--baseq_threshold`: Minimum BASEQ threshold for pass, scored on first quartile of all reads per base (default = 30).
- `--mapq_threshold`: Minimum MAPQ score threshold for pass, scored on first quartile of all reads per base (default = 30).
- `--visualize`: Flag to generate per-target level plots for each stat.
- `--output_raw_mpileup`: Flag to output raw mpileup file.
- `--mpileup_baseq_min`: Adjustment for minimum baseq for base to be considered valid & extracted (default = 10).
- `--mpileup_mapq_min`: Adjustment for minimum mapq for base to be considered valid & extracted (default = 1).


### Target Evaluation Output

**Directory Structure:**

For example, when `--output_raw_mpileup` and `--visualize` is flagged:
```bash
<output_dir>
└── target_eval_results
    ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.per_base.parsed.labelled.scored.txt                     # Per-base output
    ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt   # Per-target output
    ├── PacBio_MSH3_1_reads_GM24385_IX00001.mpileup.raw.txt                                                 # Raw mpilup output
    ├── plot_BASEQ_Q1_Q1.png                # Per-target plot baseQ
    ├── plot_COVERAGE_Q1.png                # Per-target plot coverage
    ├── plot_MAPQ_Q1_Q1.png                 # Per-target plot mapQ
    ├── summary_per_base_median.scored.txt  #`Per-base aggregated across libraries
    ├── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.per_base.parsed.labelled.scored.txt                    # Per-base output
    ├── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.per_base.parsed.labelled.target_aggregated.scored.txt  # Per-target output
    └── WGS_HCP_MSH3_2_reads_GM24385_IX00000.mpileup.raw.txt                                                # Raw mpilup output
```

**Example Output:**

*NOTE: output files are 1-indexed*

1. Per-base output
```bash
#CHROM	POS	TRACT	POOL	COVERAGE	BASEQ_MED	BASEQ_Q1	MAPQ_MED	MAPQ_Q1	SCORE
chr5	664	MSH3_NM_002439_EXON01_2	IX00001	1	40	40	60	60	FAIL
chr5	665	MSH3_NM_002439_EXON01_2	IX00001	1	40	40	60	60	FAIL
...
```
2. Per-target output
```bash
#CHROM	POS	TRACT	POOL	COVERAGE_Q1	BASEQ_Q1_MED	BASEQ_Q1_Q1	MAPQ_Q1_MED	MAPQ_Q1_Q1	SCORE
chr5	NA	MSH3_NM_002439_EXON01_1	IX00001	0	NA	0	NA	0	FAIL
chr5	NA	MSH3_NM_002439_EXON01_2	IX00001	0	NA	0	NA	0	FAIL
```
3. Per-base aggregated across libraries
```bash
#CHROM	POS	TRACT	POOL	COVERAGE_MED	BASEQ_MED_MED	BASEQ_MED_Q1	MAPQ_MED_MED	MAPQ_MED_Q1	SCORE
chr5	664	MSH3_NM_002439_EXON01_2	AGGREGATE	0.5	20	20	30	30		FAIL
chr5	665	MSH3_NM_002439_EXON01_2	AGGREGATE	0.5	20	20	30	30		FAIL
...
```


### Target Evaluation Scoring Explained
Scoring is conducted based on the following metrics for each file

1. Per-base
   - COVERAGE: Each base has a coverage count of all aligned reads covering the base that pass the mpileup requirements.
           These requirements can be adjusted using`--mpileup_baseq_min` and `--mpileup_mapq_min`.
   - BASEQ_Q1: Calculated as the first quartile of all baseQ scores at this loci of reads in COVERAGE.
   - MAPQ_Q1: Calculated as the first quartile of all mapQ score of reads in COVERAGE.


2. Per-target
   - COVERAGE_Q1: First quartile of the coverages of all bases within the target region.
   - BASEQ_Q1_Q1: First quartile of all BASEQ_Q1s of all bases within the target region.
   - MAPQ_Q1_Q1: First quartile of all MAPQ_Q1s of all bases within the target region.

   Overall, a `FAIL` here suggests that more than 75% of the bases within this target-region failed on one or more of the 3 metrics.


3. Per-base aggregated across libraries
   - COVERAGE_MED: Median coverage of this loci across all libraries.
   - BASEQ_MED_Q1: Median BASEQ_Q1s of this loci across all libraries.
   - MAPQ_MED_Q1: Median MAPQ_Q1s of this loci across all libraries.
