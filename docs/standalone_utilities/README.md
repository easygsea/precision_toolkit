# Standalone Utilities

- [Convert Multi-Sample VCF File into Single-Sample VCF files](#convert-multi-sample-vcf-file-into-single-sample-vcf-files)
- [Count Variants By Size](#count-variants-by-size)
- [Generate Standardized BED](#generate-standardized-bed)
- [Jira Table Converter](#jira-table-converter)
- [Manual Diagnostic Metric Curation](#manual-diagnostic-metric-curation)
- [Structural Variant VCF Liftover](#structural-variant-vcf-liftover)

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

The `generate-standardized-bed` tool reformats a BED file in BED6+4 format into a 4-column BED file and standardizes feature names. As intron features are not typically included in BED files, users can enable intron calculation using `--output_introns`.

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

`exon_number`, if present in the attributes, is dynamically zero-padded based on the total number of genomic features present for the gene/transcript:

- For genes/transcripts with <10 features: no leading zeros
- For 10-99 features: one leading zero (e.g. `<feature>01`)
- For 100-999 features: two leading zeros (e.g. `<feature>001`)
- Etc.

For features without `exon_number`, the feature name will simply be `<gene_symbol>_<refseq_accession>_<feature>`.

Usage:
```bash
generate-standardized-bed --bed_file <BED> --gene_list <TARGET GENES FILE> --output_folder <OUTPUT DIRECTORY>
```

## Jira Table Converter

The `jira-table` tool converts structured data files (CSV, TSV, Excel, and JSON) into a neatly formatted JIRA table.

Usage:
```bash
jira-table <PATH/TO/INPUT_FILE> --heading <HEADING> --summary <SUMMARY>
```

## Manual Diagnostic Metric Curation

We provide a handy tool to manually curate a diagnostic metric (concordance, sensitivity, precision, or f1_score) after the variant benchmark (diagnostic metrics) workflow has been run.

`manual-diagnostic-metric-curation`

To view the help message, run:
```bash
apptainer exec <path/to/clinical_tools_latest.sif> manual-diagnostic-metric-curation -h
```

Example usage is provided in the [Variant Benchmark](../workflows/variant_benchmark.md#diagnostic-metrics-manual-curation) manual.

## Structural Variant VCF Liftover

The `liftover_sv_vcf.sh` tool enables conversion of structural variant VCF files between different genome assemblies (e.g., from hg19 to hg38) by leveraging the UCSC liftOver utility.

Usage:
```bash
<path/to/clinical_tools/src/bin/>liftover_sv_vcf.sh input.vcf output.vcf chain_file.chain
```

For detailed documentation and examples, see [Structural Variant VCF Liftover Tool](liftover_sv_vcf.md).
