# Standalone Utilities

- [Compile DRAGEN Metrics](#compile-dragen-metrics)
- [Convert Multi-Sample VCF File into Single-Sample VCF files](#convert-multi-sample-vcf-file-into-single-sample-vcf-files)
- [Count Variants By Size](#count-variants-by-size)
- [Generate Standardized BED](#generate-standardized-bed)
- [Jira Table Converter](#jira-table-converter)
- [Manual Diagnostic Metric Curation](#manual-diagnostic-metric-curation)
- [Plot Contamination VAFs](#plot-contamination-vafs)
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

`compile-dragen-metrics` will look for the source file `<RGSM>_mapping_metrics.csv` in each directory passed to `--analysis-dirs` and extract values for the metrics `TOTAL_PF_READS`, `MAPPED_READS`, `PCT_CHIMERIC_READS_BASE`, and `PCT_CONTAMINATION_EST`. As many metrics expressed as percentages are reported as counts in DRAGEN source files, further calculation is required. These metrics are specified with the `_BASE` suffix (e.g. `PCT_CHIMERIC_READS_BASE`), indicating that the reported count must be divided by `MAPPED_READS` to compute the corresponding percentage.

Extracted QC metrics are written to `<RGSM>_MetricsOutput.tsv`, with metric names and values formatted according to attributes defined in the `Constants` section of the configuration file. Common attributes include:
* `FACTOR`: scale **factor**
* `RAD`: **r**ounding **a**t **d**isplay
* `UOM`: **u**nit **o**f **m**easurement

Metrics will also be classified as either "Monitoring" or "Production", with "Monitoring" as the default. Metrics with failure thresholds defined in the `Failures` section are classified as "Production", and assigned "Pass" or "Fail" status depending on whether the threshold condition is met.

Usage:
```bash
compile-dragen-metrics --metrics-json-config <json_config> --analysis-dirs <dragen_backbone_analysis_dir> [<dragen_backbone_analysis_dir> ...] --rgsm <rgsm> --output-folder <output_folder>
```

Example output:
```bash
Metric (UOM)	Category	<RGSM>	FailureDirection	Threshold   Status
TOTAL_PF_READS (Count)	Monitoring  100 None	None	None
PCT_CONTAMINATION_EST (%)	Production  0.01    greater_than    0.02	Pass
PCT_CHIMERIC_READS (%)	Monitoring	25.00	None	None	None
```

For detailed documentation of how to prepare the configuration file, see [Summarizing DRAGEN QC metrics with `compile-dragen-metrics` and `plot-dragen-metrics`](compile_and_plot_dragen_metrics.md).

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

## Plot Contamination VAFs

The `plot-contamination-vafs` tool plots variant allele frequencies (VAFs) of germline variants, facilitating differentiation of samples with true vs. false-positive contamination estimates. As germline variants are expected to have VAFs clustered at 0, 0.5, and 1, deviations from this pattern suggest potential contamination. More specifically, presence of *scattered* VAFs outside of 0.5 is indicative of true contamination. Refer to [DRAGEN's documentation](https://help.tso500software.illumina.com/dragen-tso-500-guides/dragen-tso-500-v2.6/overview-1/quality-control/contamination#contamination-score-interpretation) for example plots and interpretation.

Valid inputs include DRAGEN's `*.tmb.trace.tsv` and `*.hard.filtered.vcf.gz`, where germline variants are flagged with `Germline_DB` or `Germline_Proxi` status. Small variant VCFs from other callers are also supported, provided that either `--population-variants-vcf` or `--population-markers-vcf` is supplied. This enables inference of germline SNVs via intersection of variant calls with population markers, defined as common bi-allelic SNPs with AF ≥ a configurable threshold (`--population-snp-af-threshold`, default: `0.01`). AF values are extracted from the VCF column and tag indicated by `--population-vcf-af-tag` (default: `'INFO/AF'`). These marker loci can be derived internally from a population variants VCF (e.g. [1000 Genomes](https://hgdownload.soe.ucsc.edu/gbdb/hg38/1000Genomes/)) or supplied directly as a precomputed population markers VCF.

To ensure VAFs from confident calls are plotted, variant calls in VCF format will first be filtered based on the FILTER column. Specifically, records with FILTER values matching those in the comma-separated list passed to `--variant-vcf-apply-filters` (default: `PASS`) are retained. By default, VAFs are extracted from the `FORMAT/AF` tag; however, a different tag can be specified using `--variant-vcf-af-tag`.

Usage:
```bash
plot-contamination-vafs --variant-calls <dragen_tmb_trace_tsv|variant_calls_vcf> --output-folder <output_folder> [--variant-vcf-apply-filters <filter_value1,filter_value2,...>] [--variant-vcf-af-tag <FORMAT|INFO>/<tag>] [--population-variants-vcf <population_variants_vcf> | --population-markers-vcf <population_markers_vcf>] [--population-vcf-af-tag <FORMAT|INFO>/<tag>] [--population-snp-af-threshold <min_af>]
```

Example usage:
```bash
# DRAGEN's *.tmb.trace.tsv
plot-contamination-vafs \
    --variant-calls NA12878_Coriell_IX13680_F161339.tmb.trace.tsv \
    --output-folder contamination_vaf_plot

# VCF of variant calls and a VCF of population variants from which population markers can be derived
plot-contamination-vafs \
    --variant-calls NA12878_Coriell_IX13680_F161339.hard-filtered.vcf \
    --variant-vcf-apply-filters 'PASS' \
    --variant-vcf-af-tag 'FORMAT/AF' \
    --population-variants-vcf population_variants.vcf \
    --population-vcf-af-tag 'INFO/AF' \
    --population-snp-af-threshold 0.01 \
    --output-folder contamination_vaf_plot

# VCF of variant calls and a VCF of population markers
plot-contamination-vafs \
    --variant-calls NA12878_Coriell_IX13680_F161339.hard-filtered.vcf \
    --variant-vcf-apply-filters 'PASS' \
    --variant-vcf-af-tag 'FORMAT/AF' \
    --population-markers-vcf population_markers.vcf \
    --output-folder contamination_vaf_plot
```

## Plot DRAGEN Metrics

The `plot-dragen-metrics` tool generates summary plots for backbone QC metrics in the `MetricsOutput.tsv` file(s) output by DRAGEN. Plot settings (i.e. metrics to plot, thresholds, proposed thresholds) are specified in a JSON-formatted configuration file. If `compile-dragen-metrics` was used previously, the same configuration file can be supplied to `plot-dragen-metrics` — refer to the [`compile-dragen-metrics` documentation](#compile-dragen-metrics) for an example.

Of particular importance for `plot-dragen-metrics` is the `ReportedMetrics` section, which specifies the metrics to plot, and the following attributes defined in the `Constants` section, as these are used to annotate plots with threshold lines:

- `LSL`: guideline-suggested lower specification limit
- `USL`: guideline-suggested upper specification limit

QC failure thresholds defined in the `Failures` section are also displayed on the plots.

Metrics can be aggregated across runs and plotted together if multiple `MetricsOutput.tsv` files are supplied to `--metrics-files`. Within these plots, samples can be grouped and colored by a column specified by `--group-by` if a [FASTQ list](https://help.dragen.illumina.com/product-guide/dragen-v4.4/dragen-host-software#multiple-fastq-input-files) is passed to `--fastq-list`. This FASTQ list should contain columns mapping each `RGSM` to its corresponding group.

Additionally, `RGSM` plot labels can be truncated when `--truncate-rgsm` is set. This is used in conjunction with `--truncate-rgsm-delim` (default: '_') and `--truncate-rgsm-index` (default: 1). These arguments can help simplify long RGSM labels and group samples in the plots.

By default, samples appear alphabetically in the plots. Use `--sort-by` to order samples in descending order by a particular metric. The same ordering is applied across all plots. Note that the metric name supplied to `--sort-by` must match the labels used in the plots, including the units (e.g., `--sort-by 'PCT_TARGET_250X (%)'`).

Usage:
```bash
plot-dragen-metrics --metrics-json-config <config_json> --metrics-files <metrics_output_tsv> [<metrics_output_tsv> ...] --output-folder <output_folder> [--fastq-list <dragen_fastq_list_csv>] [--group-by <column_name_from_fastq_list>] [--sort-by <metric_from_metrics_files>] [--truncate-rgsm] [--truncate-rgsm-delim <delimiter_used_to_split_rgsm>] [--truncate-rgsm-index <number_of_fields_to_retain>]
```

For detailed documentation of how to prepare the configuration file, see [Summarizing DRAGEN QC metrics with `compile-dragen-metrics` and `plot-dragen-metrics`](compile_and_plot_dragen_metrics.md).

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
