# Standalone Utilities

- [Manual Diagnostic Metric Curation](#manual-diagnostic-metric-curation)
- [Convert Multi-Sample VCF File into Single-Sample VCF files](#convert-multi-sample-vcf-file-into-single-sample-vcf-files)
- [Count Variants By Size](#count-variants-by-size)

## Manual Diagnostic Metric Curation

We provide a handy tool to manually curate a diagnostic metric (concordance, sensitivity, precision, or f1_score) after the variant benchmark (diagnostic metrics) workflow has been run.

`manual-diagnostic-metric-curation`

To view the help message, run:

```bash
apptainer exec <path/to/clinical_tools_latest.sif> manual-diagnostic-metric-curation -h
```

Example usage is provided in the [Variant Benchmark](../workflows/variant_benchmark.md#diagnostic-metrics-manual-curation) manual.

## Convert Multi-Sample VCF File into Single-Sample VCF files

The `convert-multi-sample-vcf` tool allows to convert multi-sample VCF file into a folder of multiple single-sample VCFs for better analysis of each individual sample.

Usage
```commandline
convert-multi-sample-vcf <PATH/TO/VCF> --output-folder <OUTPUT NAME> (--suffix <SUFFIX FOR OUTPUT FILES>)
```

## Count Variants By Size

`count-variants-by-size` is a tool that counts the number of variants in a VCF file by size.

Example usage:
```
count-variants-by-size \
tests/standalone/data/two_sample.vcf \
--size-stratification 1 25 50 \
--count-occurrences
```

Example output:
```
1: 200
2-25: 25
26-50: 2
>50: 0
```
