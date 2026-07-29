# Precision Toolkit Update Log

## Version History

---

### v1.3.1 - 2026-XX-XX

---

### v1.3.0 - 2026-06-16
- Rename the project from Clinical Tools to Precision Toolkit (`clinical_tools` -> `precision_toolkit`).

---

### v1.2.2 - 2026-06-10
- New Standalone Utility: Add `plot-contamination-vafs` to visualize germline variant VAFs for contamination assessment.
- Improvement: Add `normalization_method` enum option for normalizing by median or mean in the `NORMALIZE_COVERAGE_TO_TARGET` process.
- Improvement: Ensure `uv.lock` is up to date with `pyproject.toml` via `uv sync --locked` in CI/CD and a `uv-lock` pre-commit hook.
- Improvement: Extract enum validation duplicated logic from `target_evaluation.nf` and `variant_benchmark.nf` to `modules/utils/main.nf`.
- Improvement: Remove main.nf filename in include paths to use module include to import modules
- Bugfix: Include `.venv` in the copy step into main when cloning to deployment.

---

### v1.2.1 - 2026-04-21
- Feature: Add per library QC report generation process to summarize base and target failures in `cohort_qc_report.tsv`.
- Feature: Add support for Truvari in variant benchmark workflow.
- Feature: Add plot to visualize per-base library fail rates, highlighting bases where the fraction of failing libraries exceeds a threshold specified by `--cohort_percent_library_fail_threshold` (default: 0.25).
- Improvement: Add `length` tag to contig header lines in lifted VCF output by `liftover_sv_vcf.sh`.
- Improvement: Add option to group and color signal correlation plots by run tag using `--color_source run` (renamed from old `--filter_source` parameter) and `--run_pattern`, as well as `--color_palette` metric to set color preferences.
- Improvement: Optimize Nextflow test execution by parallelizing workflows and symlinking input files.
- Improvement: Refactor container creation to use a cached base image.

---

### v1.2.0 - 2026-03-27
- Improvement: Move `src/bin` to `src/clinical_tool/cli`.
- Improvement: Replace Poetry with uv for managing the environment and upgrade Python to 3.13.12.
- Improvement: Retire `apptainer.def` file since Apptainer image is built from Docker image.
- Improvement: Standardize docstrings across dataclasses and functions to follow Google-style conventions.
- Improvement: Update Dockerfile to use a multi-stage build, caching the pysam compilation step.

---

### v1.1.4 - 2026-03-16
- New Standalone Utility: Added `plot-dragen-metrics` to plot backbone QC metrics in DRAGEN's `MetricsOutput.tsv`.
- Feature: Added functionality to compile a systemic fail tract (`common_fail_regions.bed`) using cohort-level base-specific fail data. Threshold can be adjusted with `--cohort_percent_library_fail_threshold` parameter (default: 0.25).
- Improvement: Added support for parsing metrics from JSON files in `compile-dragen-metrics`.
- Improvement: Enabled multiple inputs to `--analysis-dirs` (formerly `--analysis-dir`) in `compile-dragen-metrics`.
- Improvement: Updated workflow to allow direct CRAM injection into mpileup, bypassing intermediate BAM generation and reducing overhead.
- Bugfix: Fixed sorting inconsistency during plotting (now deterministic).
- Bugfix: Fixed tract generation bug causing off-by-one error (indexing concordance now aligned).

---

### v1.1.3 - 2026-01-26
- New Standalone Utility: Added `compile-dragen-metrics` to extract and format backbone QC metrics from DRAGEN output files.
- New Standalone Utility: Added `fetch-pull-requests` to fetch pull requests using a given bitbucket url, project, repo (optional), and authentication token.
- Improvement: Added arguments in `generate-standardized-bed` to optionally adjust CDS/exon boundaries and filter for genes/features of interest.
- Bugfix: Removed `# type: ignore` by updating `.pre-commit-config.yaml` to account for these types, and updated test files accordingly to pass pre-commit and testing.

---

### v1.1.2 - 2025-12-16
- Hotfix: Sorted scored metrics file prior to `bedtools merge` when generating tracts.

---

### v1.1.1 - 2025-12-10
- New Standalone Utility: Added `generate-standardized-bed` to reformat BED files in BED6+4 format into a 4-column BED file and standardize feature names.
- Feature: Introduced coverage normalization option in target evaluation workflow.
- Feature: Introduced tract building functionality to target evaluation workflow.
- Improvement: Added two arguments in `jira-table` to control float formatting and text output formatting.
- Improvement: Removed redundant slurm partition setting and removed time limit for slurm execution in `nextflow.config`.
- Improvement: Restructured target evaluation directory for ease of access when working with large datasets.
- Improvement: Reworked target evaluation workflow with more intuitive and robust scoring and analysis. Added three arguments to allow fine-tuning of fail tolerance and percentile output.
- Improvement: Set time limit for local execution in `nextflow.config`.
- Bugfix: Fixed circular dependency in resource allocation.
- Bugfix: Fixed container link in local deployment's `nextflow.config`.

---

### v1.1.0 - 2025-10-15
- New Workflow: Introduced target evaluation workflow for analyzing per-base stats across target regions.
- New Standalone Utility: Added `jira-table` to convert structured data files into a formatted JIRA table.
- New Standalone Utility: Added `liftover_sv_vcf.sh` helper.
- Feature: Added GitHub Actions to automatically sync changes from Bitbucket.
- Improvement: Refactored Bamboo plan to build images via Docker build.
- Improvement: Specified container version in `nextflow.config`.
- Improvement: Removed redundant version tracking.
- Bugfix: Cleaned up redundant text in `Dockerfile`.
- Bugfix: Fixed the deployment stage to point the container built instead of remote.
- Bugfix: Removed unused fixture in `tests/unit/test_diagnostic_metrics.py`.
- Applied GPL-3.0 license.

---

### v1.0.1 - 2025-07-12
- Feature: Added `--all-data-csv` export option for easier data wrangling and plotting.

---

### v1.0.0 - 2025-07-11
- New Workflow: Introduced variant benchmarking workflow for variant calling accuracy analysis.
- New Workflow: Introduced signal correlation workflow for comparing variant allele frequencies.
- New Standalone Utility: Included initial set of standalone utility tools: `convert-multi-sample-vcf`, `count-variants-by-size`, and `manual-diagnostic-metric-curation`.
