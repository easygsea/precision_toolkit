# Signal Correlation

The signal correlation workflow extracts signal values (e.g. VAF, AF, LR) from the truth and query VCF files and plots the signal values against each other.

## Quick Start

VAF/AF correlation with regression line, excluding spurious variants:
```bash
nextflow run main.nf \
--workflows signal_correlation \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--truth_signal VAF \
--query_signal AF \
--spurious_variants_vcf <path/to/spurious_variants_vcf> \
--xlim="0 1" \
--ylim="0 1" \
--show_regression true
```

## Signal Correlation Parameters

**Required Parameters:**
- `--truth_dir`: The directory containing truth VCF files (ground truth). These must be named as <sample>.truth.vcf or <sample>.truth.vcf.gz.
- `--query_dir`: The directory containing query VCF files (the test or experimental dataset). These must be named as <sample>.query.vcf or <sample>.query.vcf.gz.
- `--truth_signal`: The signal to extract from the truth VCF files.
- `--query_signal`: The signal to extract from the query VCF files.

**Optional Parameters:**
- `--spurious_variants_vcf`: The VCF file containing spurious variants to exclude.
- `--collapse`: The collapse option for bcftools isec.
- `--xlim`: The x-axis limits. Example usage: --xlim="0 1".
- `--ylim`: The y-axis limits. Example usage: --ylim="0 1".
- `--show_regression`: Show the regression line.
- `--color_source`: The column to use for grouping and coloring in the signal correlation plots ('', 'truth', 'query', or 'run').
    - If 'truth' is selected, the pipeline will group and color variant calls by the FILTER column in the truth VCFs.
    - If 'query' is selected, the pipeline will group and color variant calls by the FILTER column in the query VCFs.
    - If 'run' is selected, the workflow will extract tags from VCF filenames using the pattern provided in `--run_pattern`, grouping and coloring variants on the extracted tags.
- `--run_pattern`: If 'run' is selected for `--color_source`, provide a pattern to use for extracting run tags from the name of truth/query files (e.g., 'AB\\d{5}' or "AB\\\d{5}"). This can be creatively used for other tags in the vcf names as well (e.g., year of extraction, sample groups, sources, batches).
