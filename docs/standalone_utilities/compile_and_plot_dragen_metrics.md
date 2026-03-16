# Summarizing DRAGEN QC metrics with `compile-dragen-metrics` and `plot-dragen-metrics`

DRAGEN outputs several QC reports for each sample, uniquely identified by its `RGSM`, which contains detailed metrics for each activated module of the pipeline. The specific reports generated depends on the modules that are enabled, but common reports include `cnv_metrics.csv`, `coverage_metrics.csv`, `mapping_metrics.csv`, and `umi_metrics.csv`.

While these reports are comprehensive, it can be tedious to locate specific metrics of interest across multiple files. The `compile-dragen-metrics` Python script can be used to extract selected metrics for a given `RGSM` (`--rgsm`) and consolidate them into a single report, `<RGSM>_MetricsOutput.tsv`, based on a user-provided JSON configuration file (`--metric-config-json`).

After combining each sample's `<RGSM>_MetricsOutput.tsv` into an aggregated report, `plot-dragen-metrics` can be used to generate summary plots of each QC metric, facilitating comparison across samples. The same JSON configuration file can be supplied to `plot-dragen-metrics`, which also specifies threshold values used to annotate the plots.

## Preparing the JSON-formatted configuration file (`--metrics-json-config`)

This file indicates which QC metrics should be extracted from DRAGEN's QC reports. It's primarily used to:

- Specify the source file of each metric (e.g. `mapping_metrics.csv`, `umi_metrics.csv`, etc.) and the field to extract the value from
- Define the output metric name and formatting attributes
- Set failure thresholds and suggested limits for fail/pass classification and plot annotation

### DRAGEN QC report structure

Most modules output metrics in CSV format which typically consist of five columns:

1. Section
2. Subsection (e.g. read group or sample)
3. Metric
4. Value 1 (Count/Ratio/Minutes)
5. Value 2 (Percentage/Seconds)

Below is an example of the `mapping_metrics.csv` contents:

```csv
MAPPING/ALIGNING SUMMARY,,Total input reads,53688528,100.00
MAPPING/ALIGNING SUMMARY,,Number of duplicate marked reads,0,0.00
MAPPING/ALIGNING SUMMARY,,Number of duplicate marked and mate reads removed,NA
MAPPING/ALIGNING SUMMARY,,Number of unique reads (excl. duplicate marked reads),53688528,100.00
MAPPING/ALIGNING SUMMARY,,Reads with mate sequenced,53688528,100.00
MAPPING/ALIGNING SUMMARY,,Reads without mate sequenced,0,0.00
MAPPING/ALIGNING SUMMARY,,QC-failed reads,0,0.00
MAPPING/ALIGNING SUMMARY,,Mapped reads,51138880,95.25
# ... additional summary metrics ...
...
# ... summary metrics per read group ...
MAPPING/ALIGNING PER RG,22M2GWLT4_lane6_ACTCGGCAAT-TTCAGTTGTC,Total reads in RG,53688528,100.00
MAPPING/ALIGNING PER RG,22M2GWLT4_lane6_ACTCGGCAAT-TTCAGTTGTC,Number of duplicate marked reads,0,0.00
MAPPING/ALIGNING PER RG,22M2GWLT4_lane6_ACTCGGCAAT-TTCAGTTGTC,Number of duplicate marked and mate reads removed,NA
MAPPING/ALIGNING PER RG,22M2GWLT4_lane6_ACTCGGCAAT-TTCAGTTGTC,Number of unique reads (excl. duplicate marked reads),53688528,100.00
MAPPING/ALIGNING PER RG,22M2GWLT4_lane6_ACTCGGCAAT-TTCAGTTGTC,Reads with mate sequenced,53688528,100.00
MAPPING/ALIGNING PER RG,22M2GWLT4_lane6_ACTCGGCAAT-TTCAGTTGTC,Reads without mate sequenced,0,0.00
MAPPING/ALIGNING PER RG,22M2GWLT4_lane6_ACTCGGCAAT-TTCAGTTGTC,QC-failed reads,0,0.00
MAPPING/ALIGNING PER RG,22M2GWLT4_lane6_ACTCGGCAAT-TTCAGTTGTC,Mapped reads,51138880,95.25
...
```

There are also a few modules that will output metrics in JSON format. An example is shown below of the `contamination.json` contents output by the TSO500 pipeline:

```json
{
  "ContaminationScore": 2.4328866636327775,
  "ContaminationLevel": 0.014,
  "CONTAMINATION_P_VALUE": "NaN",
  "SNPsUsed": [
    {
      "CHROM": "chr4",
      "POS": 143043397,
      "REF": "G",
      "ALT": "A",
      "DP": 144,
      "AF": 0.007,
      "Q": 2.4328866636327775
    }
  ]
}
```

### Configuration file template

Templates for both CSV and JSON data sources are included. The two are identical except for the `Mappings` section - columns and row indices are specified for CSV source files, whereas JSON path expressions are specified for JSON source files.

```json
{
    "ReportedMetrics": [
        <OUTPUT_METRIC_NAME>,
        ...
    ],
    "DataSources": {
        <SECTION_IN_DRAGEN_CSV>: {
            "SourceName": <SOURCE_FILE>,
            "SourceType": "CSV",
            "AllowSourceFileToBeMissing": <bool>,
            "DefaultValueOnMissing": null | <float>,
            "Mappings": {
                <OUTPUT_METRIC_NAME>: "{'Row':[<METRIC_IN_DRAGEN_CSV>, <ROW_INDEX>],'Col':<COL_INDEX>}",
                ...
            },
            "Constants": {
                <OUTPUT_METRIC_NAME>.UOM: <str>,        // unit of measurement
                <OUTPUT_METRIC_NAME>.RAD: <int>,        // number of decimal places to display
                <OUTPUT_METRIC_NAME>.FACTOR: <float>,   // scale factor
                <OUTPUT_METRIC_NAME>.LSL: <float>,      // guideline-suggested lower specification limit
                <OUTPUT_METRIC_NAME>.USL: <float>,      // guideline-suggested upper specification limit
                ...
            },
            "FactorOperations": {
                <OUTPUT_METRIC_NAME>.FACTOR: "add" | "multiply" | "divide" | "subtract",
                ...
            },
            "Failures": {
                <OUTPUT_METRIC_NAME>.THRESHOLD: <float>,
                <OUTPUT_METRIC_NAME>.DIRECTION: "greater_than" | "greater_than_or_equal" | "less_than" | "less_than_or_equal",
                ...
            }
        },
        <SECTION_IN_DRAGEN_JSON>: {
            "SourceName": <SOURCE_FILE>,
            "SourceType": "JSON",
            "AllowSourceFileToBeMissing": <bool>,
            "DefaultValueOnMissing": null | <float>,
            "Mappings": {
                <OUTPUT_METRIC_NAME>: "$.<METRIC_IN_DRAGEN_JSON>",
                ...
            },
            // Other sections identical to the CSV template
            ...
        },
        ...
}
```

For example, the section for `mapping_metrics.csv` in the configuration file may look something like this:

```json
{
    "ReportedMetrics": [
        "TOTAL_PF_READS",
        "PCT_ALIGNED_READS",
        "MEDIAN_INSERT_SIZE",
        "PCT_CHIMERIC_READS",
        "DNA_PCT_SOFT_CLIPPED_BASES",
        "DNA_PCT_ABOVE_Q30",
        "PCT_CONTAMINATION_EST"
    ],
    "DataSources": {
        "MAPPING/ALIGNING SUMMARY": {
            "SourceName": "mapping_metrics.csv",
            "SourceType": "CSV",
            "AllowSourceFileToBeMissing": true,
            "DefaultValueOnMissing": null,
            "Mappings": {
                "TOTAL_PF_READS": "{'Row':['Total input reads', 2],'Col':[3]}",
                "PCT_ALIGNED_READS": "{'Row':['Mapped reads', 2],'Col':[4]}",
                "MEDIAN_INSERT_SIZE": "{'Row':['Insert length: median', 2],'Col':[3]}",
                "PCT_CHIMERIC_READS_BASE": "{'Row':['Supplementary (chimeric) alignments', 2],'Col':[3]}",
                "MAPPED_READS": "{'Row':['Mapped reads', 2],'Col':[3]}",
                "DNA_PCT_SOFT_CLIPPED_BASES": "{'Row':['Soft-clipped bases', 2],'Col':[4]}",
                "DNA_PCT_ABOVE_Q30": "{'Row':['Q30 bases', 2],'Col':[4]}",
                "PCT_CONTAMINATION_EST": "{'Row':['Estimated sample contamination', 2],'Col':[3]}"
            },
            "Constants": {
                "TOTAL_PF_READS.UOM": "Count",
                "TOTAL_PF_READS.RAD": 0,
                "PCT_ALIGNED_READS.UOM": "%",
                "PCT_ALIGNED_READS.RAD": 1,
                "MEDIAN_INSERT_SIZE.UOM": "bp",
                "MEDIAN_INSERT_SIZE.RAD": 0,
                "MEDIAN_INSERT_SIZE.LSL": 70,
                "PCT_CHIMERIC_READS.UOM": "%",
                "PCT_CHIMERIC_READS.RAD": 2,
                "PCT_CHIMERIC_READS.USL": 8.0,
                "MAPPED_READS.FACTOR": 0.0001,
                "PCT_CHIMERIC_READS.FACTOR": 100,
                "DNA_PCT_SOFT_CLIPPED_BASES.UOM": "%",
                "DNA_PCT_SOFT_CLIPPED_BASES.RAD": "2",
                "DNA_PCT_ABOVE_Q30.UOM": "%",
                "DNA_PCT_ABOVE_Q30.RAD": "2",
                "PCT_CONTAMINATION_EST.FACTOR": 100,
                "PCT_CONTAMINATION_EST.UOM": "%",
                "PCT_CONTAMINATION_EST.RAD": 2
            },
            "FactorOperations": {
                "MAPPED_READS.FACTOR": "add",
                "PCT_CHIMERIC_READS.FACTOR": "multiply",
                "PCT_CONTAMINATION_EST.FACTOR": "multiply"
            },
            "Failures": {
                "PCT_CONTAMINATION_EST.THRESHOLD": 2.0,
                "PCT_CONTAMINATION_EST.DIRECTION": "greater_than"
            }
        },
        ...
    }
}
```

#### Note about the configuration file for `plot-dragen-metrics`

Some pipelines already output an aggregated QC summary report, `MetricsOutput.tsv`, such as DRAGEN's TSO500 pipeline. As this report includes the QC metrics and the associated guideline-suggested LSL/USL values, mappings of QC metrics to their corresponding source files and definition of `LSL`/`USL` attributes aren't necessary; thus, a simplified configuration file can be supplied. An example of this is shown below:

```json
{
    "ReportedMetrics": [
        "CONTAMINATION_SCORE",
        "MEDIAN_INSERT_SIZE",
        "MEDIAN_EXON_COVERAGE",
        "PCT_EXON_50X",
        "PCT_CHIMERIC_READS",
        "USABLE_MSI_SITES",
        "PCT_TARGET_HRD_50X",
        "EXCESSIVE_TF",
        "GENE_SCALED_MAD",
        "MEDIAN_BIN_COUNT_CNV_TARGET",
        "TOTAL_PF_READS",
        "MEAN_FAMILY_SIZE",
        "MEDIAN_TARGET_COVERAGE",
        "PCT_EXON_100X",
        "PCT_READ_ENRICHMENT",
        "PCT_USABLE_UMI_READS",
        "MEAN_TARGET_COVERAGE",
        "PCT_ALIGNED_READS",
        "PCT_CONTAMINATION_EST",
        "PCT_TARGET_0.4X_MEAN",
        "PCT_TARGET_50X",
        "PCT_TARGET_100X",
        "PCT_TARGET_250X",
        "PCT_SOFT_CLIPPED_BASES",
        "PCT_Q30_BASES",
        "ALLELE_DOSAGE_RATIO",
        "MEDIAN_TARGET_HRD_COVERAGE"
    ],
    "DataSources": {
        "PLACEHOLDER": {
            "SourceName": "placeholder.csv",
            "SourceType": "CSV",
            "AllowSourceFileToBeMissing": true,
            "DefaultValueOnMissing": null,
            "Mappings": {},
            "Constants": {
                "CONTAMINATION_SCORE.UOM": "NA",
                "MEDIAN_INSERT_SIZE.UOM": "bp",
                "MEDIAN_EXON_COVERAGE.UOM": "Count",
                "PCT_EXON_50X.UOM": "%",
                "PCT_CHIMERIC_READS.UOM": "%",
                "USABLE_MSI_SITES.UOM": "Count",
                "PCT_TARGET_HRD_50X.UOM": "%",
                "EXCESSIVE_TF.UOM": "NA",
                "GENE_SCALED_MAD.UOM": "Count",
                "MEDIAN_BIN_COUNT_CNV_TARGET.UOM": "Count",
                "TOTAL_PF_READS.UOM": "Count",
                "MEAN_FAMILY_SIZE.UOM": "Count",
                "MEDIAN_TARGET_COVERAGE.UOM": "Count",
                "PCT_EXON_100X.UOM": "%",
                "PCT_READ_ENRICHMENT.UOM": "%",
                "PCT_USABLE_UMI_READS.UOM": "%",
                "MEAN_TARGET_COVERAGE.UOM": "Count",
                "PCT_ALIGNED_READS.UOM": "%",
                "PCT_CONTAMINATION_EST.UOM": "%",
                "PCT_TARGET_0.4X_MEAN.UOM": "%",
                "PCT_TARGET_50X.UOM": "%",
                "PCT_TARGET_100X.UOM": "%",
                "PCT_TARGET_250X.UOM": "%",
                "PCT_SOFT_CLIPPED_BASES.UOM": "%",
                "PCT_Q30_BASES.UOM": "%",
                "ALLELE_DOSAGE_RATIO.UOM": "NA",
                "MEDIAN_TARGET_HRD_COVERAGE.UOM": "Count"
            },
            "FactorOperations": {},
            "Failures": {
                "CONTAMINATION_SCORE.THRESHOLD": 1457,
                "CONTAMINATION_SCORE.DIRECTION": "greater_than",
                "MEDIAN_INSERT_SIZE.THRESHOLD": 70,
                "MEDIAN_INSERT_SIZE.DIRECTION": "less_than",
                "MEDIAN_EXON_COVERAGE.THRESHOLD": 150,
                "MEDIAN_EXON_COVERAGE.DIRECTION": "less_than",
                "PCT_EXON_50X.THRESHOLD": 90,
                "PCT_EXON_50X.DIRECTION": "less_than",
                "PCT_CHIMERIC_READS.THRESHOLD": 8,
                "PCT_CHIMERIC_READS.DIRECTION": "greater_than",
                "TOTAL_PF_READS.THRESHOLD": 100000000,
                "TOTAL_PF_READS.DIRECTION": "less_than",
            }
        }
    }
}
```

## Basic usage

### 1. Compile specified metrics for each sample

Run `compile-dragen-metrics` for each RGSM to extract metrics from DRAGEN QC reports, resulting in a `<RGSM>_MetricsOutput.tsv`.

```bash
compile-dragen-metrics --metrics-json-config <json_config> --analysis-dir <dragen_backbone_analysis_dir> --rgsm <rgsm> --output-folder <output_folder>
```

### 2. Aggregate all samples' metrics into a single report

Before plotting, metrics from each sample need to be combined into a single file. The script below can be used to recursively find all `<RGSM>_MetricsOutput.tsv` files, extract metric values, and create an aggregated `MetricsOutput.tsv`. This can be adapted as a Nextflow process or implemented within other workflow orchestration frameworks.

```bash
#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $(basename $0) <path to recursively search for backbone metric files> <output directory>"
    exit 1
fi

# Parse arguments
backbone_analysis_dir=$1
out_dir=$2

# Define variables
aggregate_metrics_tsv="${out_dir}/MetricsOutput.tsv"
tmp_dir="${out_dir}/tmp"
mkdir -p "${tmp_dir}"

# For each sample, extract metrics from <RGSM>_MetricsOutput.tsv
while IFS= read -r sample_qc_report_dir; do
    sample=$(basename "${sample_qc_report_dir}"/*_MetricsOutput.tsv _MetricsOutput.tsv)
    cut -f2 "${sample_qc_report_dir}"/*_MetricsOutput.tsv > "${tmp_dir}/${sample}_values.txt"
done < <(find "${backbone_analysis_dir}" -type d -name "QC_report")

# Extract metric names from first file found
first_file=$(find "${backbone_analysis_dir}" -type d -name "QC_report" | head -1)
cut -f1 "${first_file}"/*_MetricsOutput.tsv > "${tmp_dir}/metric_names.txt"

# Paste all samples' metrics into a single MetricsOutput.tsv, then cleanup
paste "${tmp_dir}/metric_names.txt" "${tmp_dir}"/*_values.txt > "${aggregate_metrics_tsv}"
rm -r "${tmp_dir}"
```

### 3. Generate plots

Use `plot-dragen-metrics` with the aggregated TSV.

```bash
plot-dragen-metrics --metrics-json-config <json_config> --metrics-files <metrics_output_tsv>
```
