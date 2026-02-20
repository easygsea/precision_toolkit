# Clinical Tools Update Log

## Version History

---

### v1.1.4 - 2026-XX-XX
- New Standalone Utility: Added `plot-dragen-metrics` to plot backbone QC metrics in DRAGEN's `MetricsOutput.tsv`.

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
