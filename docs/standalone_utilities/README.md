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

By default, `refseq_accession` is parsed from the `db_xref` attribute; however, another attribute can be specified using `--attribute-key`. For features lacking the `refseq_accession` value, the feature name will be `<gene_symbol>_<feature>`.

`exon_number`, if present in the attributes together with `refseq_accession`, is optionally dynamically zero-padded (when `--zero-pad-names` is specified) based on the total number of genomic features present for the gene/transcript:

- For genes/transcripts with <10 features: no leading zeros
- For 10-99 features: one leading zero (e.g. `<feature>01`)
- For 100-999 features: two leading zeros (e.g. `<feature>001`)
- Etc.

For features without `exon_number`, the feature name will simply be `<gene_symbol>_<refseq_accession>_<feature>`.

Usage:
```bash
generate-standardized-bed --bed-file <bed> --output-folder <output_folder> [--attribute-key <refseq_accession_attribute_key>] [--gene-list <target_gene_file>] [--output-introns] [--zero-pad-names]
```

Example output:
```bash
chrX	154021572	154031450	MECP2_NM_001110792.2_EXON3
chrX	154021572	154031450	MECP2_NM_004992.4_EXON4
chrX	154021572	154097717	MECP2_NM_001110792.2_TRANSCRIPT
chrX	154021572	154097717	MECP2_NM_004992.4_TRANSCRIPT
chrX	154021572	154097717	MECP2_GENE
chrX	154030366	154030369	MECP2_NP_001104262.1_STOP_CODON3
chrX	154030366	154030369	MECP2_NP_004983.1_STOP_CODON4
chrX	154030369	154031450	MECP2_NP_001104262.1_CDS3
chrX	154030369	154031450	MECP2_NP_004983.1_CDS4
chrX	154032206	154032557	MECP2_NP_001104262.1_CDS2
chrX	154032206	154032557	MECP2_NP_004983.1_CDS3
chrX	154032206	154032557	MECP2_NM_001110792.2_EXON2
chrX	154032206	154032557	MECP2_NM_004992.4_EXON3
chrX	154092183	154092209	MECP2_NP_004983.1_CDS2
chrX	154092183	154092307	MECP2_NM_004992.4_EXON2
chrX	154092206	154092209	MECP2_NP_004983.1_START_CODON2
chrX	154097603	154097665	MECP2_NP_001104262.1_CDS1
chrX	154097603	154097717	MECP2_NM_001110792.2_EXON1
chrX	154097603	154097717	MECP2_NM_004992.4_EXON1
chrX	154097662	154097665	MECP2_NP_001104262.1_START_CODON1
```

### Interpretation of `exon_number`

According to [Gencode's GTF format documentation](https://www.gencodegenes.org/pages/data_format.html), `exon_number` is a key found in the attributes field of all features except genes and transcripts. This integer value indicates the exon position in the transcript from its 5' end. Thus, in the example above, `*_START_CODON2` indicates that the start codon for this transcript is in exon 2 and `_STOP_CODON4` indicates that the stop codon is in exon 4.

For detailed documentation of how to use this tool to generate target BED files, see [BED Standardization Tool](generate_standardized_bed.md).

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
