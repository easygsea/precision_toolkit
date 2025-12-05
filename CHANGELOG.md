# Clinical Tools Update Log

## Version History

### v1.1.1 - 2025-11-05
- New Standalone Utility: Added new utility to reformat BED files in BED6+4 format into a 4-column BED file and standardizes feature names.
- Feature: Introduced coverage normalization option in target evaluation workflow.
- Feature: Introduced track building functionality to target evaluation workflow.
- Improvement: Added two arguments in jira-table to control float formatting and text output formatting.
- Improvement: Removed redundant slurm partition setting and removed time limit for slurm execution in nextflow.config.
- Improvement: Restructured target evaluation directory for ease of access when working with large datasets.
- Improvement: Reworked target evaluation workflow with more intuitive and robust scoring and analysis. Added three arguments to control fail tolereance and percentile output. See docs for more details.
- Improvement: Set time limit for local execution in nextflow.config.
- Bugfix: Fixed circular dependency in resource allocation.
- Bugfix: Fixed container link in local deployment's `nextflow.config`.

---

### v1.1.0 - 2025-10-15 [Released 2025-10-15]
- New Workflow: Added new target evaluation workflow for analyzing per-base stats across target regions.
- New Standalone Utility: Added new utility to convert structured data files into a formatted JIRA table.
- Feature: Added GitHub Actions to automatically sync changes from Bitbucket.
- Improvement: Refactored Bamboo plan to build images via Docker build.
- Improvement: Specify container version in `nextflow.config`.
- Improvement: Removed redundant version tracking.
- Bugfix: Cleanup in DockerFile.
- Bugfix: Removed unused fixture in `tests/unit/test_diagnostic_metrics.py`.
- Apply GPL-3.0 license

### v1.0.3 - 2025-08-26
- Bugfix: Fixed the deployment stage to point the container built instead of remote.

### v1.0.2 - 2025-08-26
- Feature: Added `liftover_sv_vcf.sh` helper.

---

### v1.0.1 - 2025-07-12 [Released 2025-07-12]
- Feature: Added `--all-data-csv` export option for easier data wrangling and plotting.

---

### v1.0.0 - 2025-07-11 [Released 2025-07-11]
- Initial release of Clinical Tools.
- New Workflow: Introduced variant benchmarking workflow for variant calling accuracy analysis.
- New Workflow: Introduced signal correlation workflow for signal analysis.
- Feature: Included initial set of standalone utility tools.
