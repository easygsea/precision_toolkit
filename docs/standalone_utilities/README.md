# Standalone Utilities

- [Compile DRAGEN Metrics](#compile-dragen-metrics)
- [Convert Multi-Sample VCF File into Single-Sample VCF files](#convert-multi-sample-vcf-file-into-single-sample-vcf-files)
- [Count Variants By Size](#count-variants-by-size)
- [Generate Standardized BED](#generate-standardized-bed)
- [Jira Table Converter](#jira-table-converter)
- [Manual Diagnostic Metric Curation](#manual-diagnostic-metric-curation)
- [Plot DRAGEN Metrics](#plot-dragen-metrics)
- [Pull Request Fetcher](#pull-request-fetcher)
- [Structural Variant VCF Liftover](#structural-variant-vcf-liftover)

## Compile DRAGEN Metrics

The `compile-dragen-metrics` tool extracts backbone QC metrics for a provided [read group sample name (RGSM)](https://help.dragen.illumina.com/product-guide/dragen-v4.4/dragen-host-software#multiple-fastq-input-files) from DRAGEN output files based on a JSON-formatted configuration file that specifies the source files (`SourceName`) and column mappings (`Mappings`). RGSM, specified with `--rgsm`, is an identifier used by DRAGEN to link multiple read groups to a single sample. This ensures that reads from the same sample, despite being distributed across multiple lanes or libraries, are processed collectively.

For example, given the following configuration file:
```json
{
    "ReportedMetrics": [
        "TOTAL_PF_READS",
        "PCT_CHIMERIC_READS",
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
                "MAPPED_READS": "{'Row':['Mapped reads', 2],'Col':[3]}",
                "PCT_CHIMERIC_READS_BASE": "{'Row':['Supplementary (chimeric) alignments', 2],'Col':[3]}",
                "PCT_CONTAMINATION_EST": "{'Row':['Estimated sample contamination', 2],'Col':[3]}"
            },
            "Constants": {
                "TOTAL_PF_READS.UOM": "Count",
                "TOTAL_PF_READS.RAD": 0,
                "MAPPED_READS.FACTOR": 0.0001,
                "PCT_CHIMERIC_READS.UOM": "%",
                "PCT_CHIMERIC_READS.RAD": 2,
                "PCT_CHIMERIC_READS.FACTOR": 100,
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
                "PCT_CONTAMINATION_EST.THRESHOLD": 0.02,
                "PCT_CONTAMINATION_EST.DIRECTION": "greater_than"
            }
        }
    }
}
```

`compile-dragen-metrics` will look for the source file `<RGSM>_mapping_metrics.csv` in the directory passed to `--analysis-dir` and extract values for the metrics `TOTAL_PF_READS`, `MAPPED_READS`, `PCT_CHIMERIC_READS_BASE`, and `PCT_CONTAMINATION_EST`. As many metrics expressed as percentages are reported as counts in DRAGEN source files, further calculation is required. These metrics are specified with the `_BASE` suffix (e.g. `PCT_CHIMERIC_READS_BASE`), indicating that the reported count must be divided by `MAPPED_READS` to compute the corresponding percentage.

Extracted QC metrics are written to `<RGSM>_MetricsOutput.tsv`, with metric names and values formatted according to attributes defined in the `Constants` section of the configuration file. Common attributes include:
* `FACTOR`: scale **factor**
* `RAD`: **r**ounding **a**t **d**isplay
* `UOM`: **u**nit **o**f **m**easurement

Metrics will also be classified as either "Monitoring" or "Production", with "Monitoring" as the default. Metrics with failure thresholds defined in the `Failures` section are classified as "Production", and assigned "Pass" or "Fail" status depending on whether the threshold condition is met.

Usage:
```bash
compile-dragen-metrics --metrics-json-config <json_config> --analysis-dir <dragen_backbone_analysis_dir> --rgsm <rgsm> --output-folder <output_folder>
```

Example output:
```bash
Metric (UOM)	Category	<RGSM>	FailureDirection	Threshold   Status
TOTAL_PF_READS (Count)	Monitoring  100 None	None	None
PCT_CONTAMINATION_EST (%)	Production  0.01    greater_than    0.02	Pass
PCT_CHIMERIC_READS (%)	Monitoring	25.00	None	None	None
```

## Convert Multi-Sample VCF File into Single-Sample VCF files

The `convert-multi-sample-vcf` tool allows to convert multi-sample VCF file into a folder of multiple single-sample VCFs for better analysis of each individual sample.

Usage:

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

## Generate Standardized BED

The `generate-standardized-bed` tool reformats a BED file in BED6+4 format into a 4-column BED file and standardizes feature names. As intron features are not typically included in BED files, users can enable intron calculation using `--output-introns`.

Specifically, the input BED file should have the following columns:

1. chrom: chromosome
2. chromStart: start position
3. chromEnd: end position
4. geneSymbol: gene symbol
5. score: score or "." if missing
6. strand: strand orientation or "." if missing
7. source: GTF/GFF source field or "." if missing
8. feature: GTF/GFF feature type
9. frame: GTF/GFF frame field or "." if missing
10. attributes: GTF/GFF attributes

This will be converted into a 4-column BED file consisting of:

1. chrom: chromosome
2. chromStart: start position
3. chromEnd: end position
4. featureName: feature name with the format `<gene_symbol>_<refseq_accession>_<feature><exon_number>`

By default, `refseq_accession` is parsed from the `transcript_id` attribute; however, another attribute can be specified using `--attribute-key`. For features lacking the `refseq_accession` value, the feature name will be `<gene_symbol>_<feature>`.

`exon_number`, if present in the attributes together with `refseq_accession`, is optionally dynamically zero-padded (when `--zero-pad-names` is specified) based on the total number of genomic features present for the gene/transcript:

- For genes/transcripts with <10 features: no leading zeros
- For 10-99 features: one leading zero (e.g. `<feature>01`)
- For 100-999 features: two leading zeros (e.g. `<feature>001`)
- Etc.

For features without `exon_number`, the feature name will simply be `<gene_symbol>_<refseq_accession>_<feature>`.

Usage:

```bash
generate-standardized-bed --bed-file <bed> --output-folder <output_folder> [--attribute-key <refseq_accession_attribute_key>] [--features <comma_separated_feature_list>] [--gene-list <target_gene_file>] [--extend-cds-to-stop] [--exclude-utrs] [--output-introns] [--zero-pad-names]
```

Example output:

```bash
chrX	154021572	154031450	MECP2_NM_001110792.2_EXON3
chrX	154021572	154031450	MECP2_NM_004992.4_EXON4
chrX	154021572	154097717	MECP2_NM_001110792.2_TRANSCRIPT
chrX	154021572	154097717	MECP2_NM_004992.4_TRANSCRIPT
chrX	154021572	154097717	MECP2_GENE
chrX	154030366	154030369	MECP2_NM_001110792.2_STOP_CODON3
chrX	154030366	154030369	MECP2_NM_004992.4_STOP_CODON4
chrX	154030369	154031450	MECP2_NM_001110792.2_CDS3
chrX	154030369	154031450	MECP2_NM_004992.4_CDS4
chrX	154032206	154032557	MECP2_NM_001110792.2_CDS2
chrX	154032206	154032557	MECP2_NM_004992.4_CDS3
chrX	154032206	154032557	MECP2_NM_001110792.2_EXON2
chrX	154032206	154032557	MECP2_NM_004992.4_EXON3
chrX	154092183	154092209	MECP2_NM_004992.4_CDS2
chrX	154092183	154092307	MECP2_NM_004992.4_EXON2
chrX	154092206	154092209	MECP2_NM_004992.4_START_CODON2
chrX	154097603	154097665	MECP2_NM_001110792.2_CDS1
chrX	154097603	154097717	MECP2_NM_001110792.2_EXON1
chrX	154097603	154097717	MECP2_NM_004992.4_EXON1
chrX	154097662	154097665	MECP2_NM_001110792.2_START_CODON1
```

### Interpretation of `exon_number`

According to [Gencode's GTF format documentation](https://www.gencodegenes.org/pages/data_format.html), `exon_number` is a key found in the attributes field of all features except genes and transcripts. This integer value indicates the exon position in the transcript from its 5' end. Thus, in the example above, `*_START_CODON2` indicates that the start codon for this transcript is in exon 2 and `_STOP_CODON4` indicates that the stop codon is in exon 4.

For detailed documentation of how to use this tool to generate target BED files, see [BED Standardization Tool](generate_standardized_bed.md).

## Jira Table Converter

The `jira-table` tool converts structured data files (CSV, TSV, Excel, and JSON) into a neatly formatted JIRA table.

Example Usage:

```bash
jira-table <PATH/TO/INPUT_FILE>
```

**Optional Parameters:**

- `--format`: Specify input file format (e.g., TSV, CSV).
- `--delimiter`: Specify a custom delimiter for parsing data.
- `--heading`: Add a table heading.
- `--summary`: Add a short description along with the table.
- `--float-format`: Control output format for float values.
- `--pretty-print`: Pad columns with spaces for readability.

## Manual Diagnostic Metric Curation

We provide a handy tool to manually curate a diagnostic metric (concordance, sensitivity, precision, or f1_score) after the variant benchmark (diagnostic metrics) workflow has been run.

`manual-diagnostic-metric-curation`

To view the help message, run:

```bash
apptainer exec <path/to/clinical_tools_latest.sif> manual-diagnostic-metric-curation -h
```

Example usage is provided in the [Variant Benchmark](../workflows/variant_benchmark.md#diagnostic-metrics-manual-curation) manual.

## Plot DRAGEN Metrics

The `plot-dragen-metrics` tool generates summary plots for backbone QC metrics in the `MetricsOutput.tsv` file(s) output by DRAGEN. Plot settings (i.e. metrics to plot, thresholds, proposed thresholds) are specified in a JSON-formatted configuration file. If `compile-dragen-metrics` was used previously, the same configuration file can be supplied to `plot-dragen-metrics` — refer to the [`compile-dragen-metrics` documentation](#compile-dragen-metrics) for an example.

Of particular importance for `plot-dragen-metrics` is the `ReportedMetrics` section, which specifies the metrics to plot, and the following attributes defined in the `Constants` section, as these are used to annotate plots with threshold lines:
- `LSL`: lower specification limit
- `USL`: upper specification limit
- `PROPOSED_LSL`: proposed lower specification limit
- `PROPOSED_USL`: proposed upper specification limit

Metrics can be aggregated across runs and plotted together if multiple `MetricsOutput.tsv` files are supplied to `--metrics-files`. Within these plots, samples can be grouped and coloured by a column specified by `--group-by` if a [FASTQ list](https://help.dragen.illumina.com/product-guide/dragen-v4.4/dragen-host-software#multiple-fastq-input-files) is passed to `--fastq-list`. This FASTQ list should contain columns mapping each `RGSM` to its corresponding group. By default, samples are grouped by `Pool`.

Usage:
```bash
plot-dragen-metrics --metrics-json-config <json_config> --metrics-files <metrics_output_tsv> [<metrics_output_tsv> ...] --output-folder <output_folder> [--fastq-list <dragen_fastq_list>] [--group-by <fastq_list_column_to_group_by>][--sort-by <metric_to_sort_by>]
```

## Pull Request Fetcher

The `fetch-pull-requests` tool fetches daily pull requests for PR reviewers.

Example Usage:
```bash
fetch-pull-requests --bitbucket_url <URL_TO_BITBUCKET> --project <PROJECT_NAME> [--repo <REPO_NAME>] --token <TOKEN>
```

## Structural Variant VCF Liftover

The `liftover_sv_vcf.sh` tool enables conversion of structural variant VCF files between different genome assemblies (e.g., from hg19 to hg38) by leveraging the UCSC liftOver utility.

Usage:

```bash
<path/to/clinical_tools/src/bin/>liftover_sv_vcf.sh input.vcf output.vcf chain_file.chain
```

For detailed documentation and examples, see [Structural Variant VCF Liftover Tool](liftover_sv_vcf.md).
