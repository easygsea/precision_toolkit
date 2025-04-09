# Standalone Utilities

- [Manual Diagnostic Metric Curation](#manual-diagnostic-metric-curation)

## Manual Diagnostic Metric Curation

We provide a handy tool to manually curate a diagnostic metric (concordance, sensitivity, precision, or f1_score) after the variant benchmark (diagnostic metrics) workflow has been run.

- `manual-diagnostic-metric-curation`

To view the help message, run:

```bash
apptainer exec <path/to/clinical_tools_latest.sif> manual-diagnostic-metric-curation -h
```

Example usage is provided in the [Variant Benchmark](../workflows/variant_benchmark.md#diagnostic-metrics-manual-curation) manual.

## Convert Multi-Sample VCF File into Single-Sample VCF files

The `convert_multi_sample_vcf` tool allows to convert multi-sample VCF file into a folder of multiple single-sample VCFs for better analysis of each individual sample.
