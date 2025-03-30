# Standalone Utilities

- [Manual Diagnostic Metrics Curation](#manual-diagnostic-metrics-curation)

## Manual Diagnostic Metrics Curation

We provide three tools to manually curate diagnostic metrics after the variant benchmark (diagnostic metrics) workflow has been run.

- `manual-variant-concordance-curation`
- `manual-sensitivity-curation`
- `manual-precision-curation`
- `manual-f1-score-curation`

To view the help message, run:

```bash
apptainer exec <path/to/clinical_tools_latest.sif> manual-variant-concordance-curation -h
apptainer exec <path/to/clinical_tools_latest.sif> manual-sensitivity-curation -h
apptainer exec <path/to/clinical_tools_latest.sif> manual-precision-curation -h
apptainer exec <path/to/clinical_tools_latest.sif> manual-f1-score-curation -h
```

Example usage is provided in the [Variant Benchmark](../workflows/variant_benchmark.md#variant-benchmark-manual-curation) manual.
