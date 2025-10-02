# Clinical Tools Update Log

## Version History

---
### v1.1.0 - 2025-09-03 [Released 2025-09-03]
- New Workflow: Added new target evaluation workflow for analyzing per-base stats across target regions.
- Bugfix: Cleanup in DockerFile.
- Bugfix: Removed unused fixture in `tests/unit/test_diagnostic_metrics.py`.
- Improvement: Refactored Bamboo plan to build images on a new server

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
