# Clinical Tools Update Log

## Version History

### v1.1.1 - 2025-10-28
- New Standalone Utility: Added new utility to reformat BED files in BED6+4 format into a 4-column BED file and standardizes feature names
- Bugfix: fixed container link in local deployment's `nextflow.config`

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
