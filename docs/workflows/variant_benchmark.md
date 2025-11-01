# Variant Benchmark (Diagnostic Metrics - Concordance, Sensitivity, Precision, F1 Score)

The variant benchmark module compares variant calls between truth and query VCF files across multiple samples using either [hap.py](https://github.com/Illumina/hap.py) or [witty.er](https://github.com/EBIvariation/witty.er), and calculates diagnostic metrics including concordance, sensitivity, precision, and F1 score.

By default, all metrics, and their confidence intervals (CIs) wherever applicable, are calculated.


## Quick Start

Small variant benchmark:
```bash
nextflow run main.nf \
--workflows variant_benchmark \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine happy \
--genome_ref <path/to/genome_ref>
```

Large variant benchmark:
```bash
nextflow run main.nf \
--workflows variant_benchmark \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine wittyer
```

Small variant benchmark excluding spurious variants:
```bash
nextflow run main.nf \
--workflows variant_benchmark \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine happy \
--genome_ref <path/to/genome_ref> \
--spurious_variants_vcf <path/to/spurious_variants_vcf>
```

Large variant benchmark excluding spurious variants:
```bash
nextflow run main.nf \
--workflows variant_benchmark \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine wittyer \
--spurious_variants_vcf <path/to/spurious_variants_vcf>
```

Custom small variant benchmark:
```bash
nextflow run main.nf \
--workflows variant_benchmark \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine happy \
--genome_ref <path/to/genome_ref> \
--diagnostic_metrics "sensitivity precision" \
--happy_options "--write-vcf --write-counts --pass-only"
```

Custom large variant benchmark:
```bash
nextflow run main.nf \
--workflows variant_benchmark \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine wittyer \
--diagnostic_metrics "sensitivity precision" \
--evaluationMode SimpleCounting \
--includedFilters PASS \
--percentDistance 0.2 \
--bpDistance 1000
```


## Variant Benchmark Manual

- [Variant Benchmark Parameters](#variant-benchmark-parameters)
- [VCF Comparison Engine Selection Guidelines](#vcf-comparison-engine-selection-guidelines)
- [Spurious Variant Filtering](#spurious-variant-filtering)
- [Variant Benchmark Output](#variant-benchmark-output)
- [Diagnostic Metrics Manual Curation](#diagnostic-metrics-manual-curation)


### Variant Benchmark Parameters

**Required Parameters:**
- `--workflows variant_benchmark`: Required parameter to run target evaluation workflow
- `--truth_dir`: The directory containing truth VCF files (ground truth). These must be named as <sample>.truth.vcf or <sample>.truth.vcf.gz.
- `--query_dir`: The directory containing query VCF files (the test or experimental dataset). These must be named as <sample>.query.vcf or <sample>.query.vcf.gz.
- `--variant_benchmark_engine`: Analysis engine for variant benchmark (`happy`, `sompy`, or `wittyer`, default: `happy`).
- `--genome_ref`: Required for hap.py: Reference genome FASTA file.

**Optional Parameters:**
- `--diagnostic_metrics`: Diagnostic metrics to calculate (default: all metrics: 'concordance sensitivity precision f1_score'). Multiple values must be passed as a quoted space-separated list. F1 score does not have a confidence interval.
- `--output_dir`: Base output directory (default: `output_clinical_tools`)
- `--variant_benchmark_dir`: Subdirectory for variant benchmark results (default: `variant_benchmark`)
- `--happy_engine`: hap.py engine to use (default: `vcfeval`) Options: `vcfeval`, `xcmp`, `scmp-distance`, `scmp-somatic`. Note: `vcfeval` mode only evaluates PASS variants as hap.py does not support `vcfeval --all-records`.
- `--happy_options`: Additional hap.py options (default: `--write-vcf --write-counts`). Must quote the string and use = to assign the value.
- `--sompy_options`: Additional som.py options (default: `--include-nonpass`). Must quote the string and use = to assign the value.
- `--wittyer_options`: Additional witty.er options (default: auto-generated from parameters below). Must quote the string and use = to assign the value.
- `--evaluationMode`: witty.er parameter: Evaluation mode (default: `CrossTypeAndSimpleCounting`) Options: `CrossTypeAndSimpleCounting`, `SimpleCounting`, `GenotypeMatching`. Note that GenotypeMatching corresponds to the Default option in witty.er documentation https://github.com/Illumina/witty.er/issues/25.
- `--includedFilters`: witty.er parameter: Comma separated list. Only variants contain these filters will be considered. Empty string ('') will include all filters (default: '').
- `--percentDistance`: witty.er parameter: Maximum allowed distance between truth and query boundaries as fraction of SV length (default: 0.3).
- `--bpDistance`: witty.er parameter: Maximum allowed distance between truth and query boundaries in base pairs (default: 5000).
- `--spurious_variants_vcf`: VCF file containing spurious variants to exclude.
- `--collapse`: Collapse option for bcftools isec (default: `none`).
- `--skip_raw`: Skip raw analysis (only available when `spurious_variants_vcf` is provided).
- `--concordance_tp`: Method for defining TP in concordance calculation. Available options: `truth` (use truth set's TP count), `query` (use query set's TP count), `min` (use minimum of truth and query TP counts, default).
- `--decimals`: Number of decimal places in rendered output (default: 2).
- `--ci_method`: Confidence interval method (default: `wilson`) Options: `agresti_coull`, `beta`, `binom_test`, `jeffreys`, `normal`, `wilson`.
- `--ci_level`: Confidence level for confidence intervals (default: 0.95).
- `--include-all-data-csv`: Option to output compiled csv for data wrangling/plotting (default: false).

**Official Parameter References:**
- [hap.py parameters](https://github.com/Illumina/hap.py/blob/master/doc/happy.md#command-line-options)
- [som.py parameters](https://github.com/Illumina/hap.py/blob/master/doc/sompy.md)
- [witty.er parameters](https://github.com/EBIvariation/witty.er/wiki/Configuration-Parameters)


### VCF Comparison Engine Selection Guidelines

1. **Use hap.py when:**
   - Your analysis requires strict matching of variant positions and alleles
   - You are working with small variants (SNPs, indels <50bp)
   - Your reference genome is well-defined and available

2. **Use som.py when:**
   - You are analyzing somatic variants (e.g. tumor-normal pairs)
   - You need to normalize variant representations before comparison

3. **Use witty.er when:**
   - You are analyzing structural variants or large indels (>50bp)
   - You need faster processing times for complex variant analysis
   - Your variants may have positional uncertainty or require fuzzy matching
   - You need advanced filtering capabilities based on variant size and type
   - Your analysis benefits from cross-type variant comparison
   - You are working with complex genomic regions or repetitive sequences

**Key Differences:**

| Feature            | hap.py                     | som.py                     | witty.er                   |
|--------------------|----------------------------|----------------------------|----------------------------|
| Variant Size       | Small variants (SNPs, indels) | Small variants (SNPs, indels) | Large variants (SVs, CNVs) |
| Matching Precision | Exact position/allele      | Normalized representation  | Fuzzy matching             |
| Speed              | Slower for small variants  | Faster than hap.py          | Faster for large variants  |
| Scalability        | Medium                     | Medium                     | High                       |
| Filtering          | Basic                      | Basic                      | Advanced by size/type      |
| Reference Genome   | Required                   | Optional                   | Optional                   |
| Best Use Case      | Small variants, germline | Small variants, somatic | Large variants, throughput |


### Spurious Variant Filtering

The pipeline supports automatic filtering of known spurious variants using [bcftools isec](https://samtools.github.io/bcftools/bcftools.html#isec) for curated statistics. To utilize this feature, prepare your spurious variant VCF file following these guidelines:

**VCF File Preparation:**
1. **File Format**: Must be a valid VCF file. Example format:

Small variants:
```
##fileformat=VCFv4.2
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr2	47414419	.	GT	G	.	.	.
chr2	47414420	.	TA	T	.	.	.
chr2	47414420	.	TAA	T	.	.	.
chr2	47414420	.	T	G	.	.	.
```
Larger variants:
```
##fileformat=VCFv4.2
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr17   43099821	DRAGEN:LOSS:chr17:43099822-43101081 N   <DEL>   .   .   .
```
2. **Chromosome Naming**: Ensure chromosome naming matches your reference genome
3. **Variant Representation**:
   - For SNPs: Use single base positions
   - For indels: Use precise start positions and correct REF/ALT representation
4. **Quality Control**:
   - Remove duplicate variants
   - Validate against reference genome
   - Include only high-confidence spurious calls
5. **bcftools isec**:
   Refer to the official [--collapse](https://samtools.github.io/bcftools/bcftools.html#isec) option for detailed guidance. Default is 'none' for identical REF and ALT alleles matching.

**Pipeline Processing Steps:**
1. Raw Variant Benchmark: Performs an initial analysis without spurious variant filtering. Use --skip_raw to bypass this step if only curated results are required.
2. Curated Variant Benchmark: Conducts a secondary analysis, excluding variants flagged as spurious in the provided VCF.

**Best Practices:**
- Maintain version control of your spurious variant VCF
- Document the source and criteria for spurious variant identification
- Update the VCF based on new findings


### Variant Benchmark Output

The pipeline records reports from variant benchmark analysis engines and generates summary tables in multiple formats, facilitating streamlined reporting:

**Directory Structure:**

For example, when spurious_variants_vcf is supplied:
```bash
<output_dir>/
    └── <variant_benchmark_dir>/
        ├── raw/                # Raw engine reports
        │   ├── happy/          # hap.py reports if using happy engine
        │   │   ├── summary.csv # hap.py statistics per sample
        │   │   ├── vcf.gz      # Detailed variant-level reports e.g. TP FN FP
        │   │   ├── ...         # Additional hap.py reports
        │   ├── sompy/          # som.py reports if using sompy engine
        │   │   ├── stats.csv   # som.py statistics per sample
        │   │   ├── scratch_sompy/ # scratch reports detailing TP/FN/FP calls
        │   └── wittyer/        # witty.er reports if using wittyer engine
        │       ├── sample1/    # Sample-specific reports
        │       │   ├── Wittyer.Stats.json  # Summary statistics in JSON format
        │       │   ├── vcf.gz              # Detailed variant-level reports e.g. TP FN FP
        │       │   ├── ...                 # Additional witty.er reports
        │       └── sample2/
        │           ├── Wittyer.Stats.json
        │           ├── vcf.gz
        │           ├── ...
        ├── curated/            # Curated engine results (after spurious variant filtering)
        │   ├── happy/
        │   │   ├── summary.csv
        │   │   ├── vcf.gz
        │   │   ├── ...
        │   ├── sompy/
        │   │   ├── stats.csv
        │   │   ├── scratch_sompy/
        │   └── wittyer/
        │       ├── sample1/
        │       │   ├── Wittyer.Stats.json
        │       │   ├── vcf.gz
        │       │   ├── ...
        │       └── sample2/
        │           ├── Wittyer.Stats.json
        │           ├── vcf.gz
        │           ├── ...
        ├── diagnostic_metrics_happy_raw_concordance.csv     # Raw variant concordance in CSV
        ├── diagnostic_metrics_happy_curated_concordance.csv # Curated variant concordance in CSV
        ├── diagnostic_metrics_happy_raw_sensitivity.csv     # Raw sensitivity in CSV
        ├── diagnostic_metrics_happy_curated_sensitivity.csv # Curated sensitivity in CSV
        ├── diagnostic_metrics_happy_raw_precision.csv       # Raw precision in CSV
        ├── diagnostic_metrics_happy_curated_precision.csv   # Curated precision in CSV
        ├── diagnostic_metrics_happy_raw_all_data.csv        # Combined raw metrics in CSV
        ├── diagnostic_metrics_happy_curated_all_data.csv    # Combined curated metrics in CSV
        ├── diagnostic_metrics_happy_combined.md             # Combined raw/curated diagnostic metrics in Markdown
        └── diagnostic_metrics_happy_combined.docx           # Combined raw/curated diagnostic metrics in Word
```

Example summary in Markdown:
```bash
# Raw Sensitivity

This table summarizes the raw sensitivity of variant calls.

| Variant Type   | Variant Filter   |   True Positive |   False Negative | Sensitivity   | CI Lower   | CI Upper   |
|----------------|------------------|-----------------|------------------|---------------|------------|------------|
| INDEL          | ALL              |              31 |               15 | 67.4%         | 54.0%      | 78.8%      |
| INDEL          | PASS             |              31 |               15 | 67.4%         | 54.0%      | 78.8%      |
| SNP            | ALL              |            1340 |               25 | 98.2%         | 97.3%      | 98.8%      |
| SNP            | PASS             |            1340 |               25 | 98.2%         | 97.3%      | 98.8%      |

# Curated Sensitivity

This table summarizes the curated sensitivity of variant calls.

| Variant Type   | Variant Filter   |   True Positive |   False Negative | Sensitivity   | CI Lower   | CI Upper   |
|----------------|------------------|-----------------|------------------|---------------|------------|------------|
| INDEL          | ALL              |              29 |                0 | 100.0%        | 88.3%      | 100.0%     |
| INDEL          | PASS             |              29 |                0 | 100.0%        | 88.3%      | 100.0%     |
| SNP            | ALL              |            1337 |                0 | 100.0%        | 99.7%      | 100.0%     |
| SNP            | PASS             |            1337 |                0 | 100.0%        | 99.7%      | 100.0%     |
```

Note that som.py does not report a filter column, so the `Variant Filter` column is always set to `NA`.

For more details on hap.py, som.py, and witty.er outputs:
- [hap.py output documentation](https://github.com/Illumina/hap.py?tab=readme-ov-file#happy)
- [som.py output documentation](https://github.com/Illumina/hap.py?tab=readme-ov-file#sompy)
- [witty.er output documentation](https://github.com/Illumina/witty.er?tab=readme-ov-file#outputs)


### Diagnostic Metrics Manual Curation

In some cases, manual curation of variant benchmark results is necessary, for example, reclassifying a false negative (FN) as a true positive (TP) after investigation. Users can run `manual-variant-concordance-curation`, `manual-sensitivity-curation`, or `manual-precision-curation` to manually update counts, after which the pipeline will recalculate the curated statistics.

Example usage:
```bash
apptainer exec -B <data_path> <path/to/clinical_tools_latest.sif> \
manual-diagnostic-metric-curation sensitivity \
--input diagnostic_metrics_happy_curated_sensitivity.csv \
--curation "SNP:PASS:TP:100" "SNP:PASS:FN:50" \
--ci-method wilson \
--ci-level 0.95 \
--output-prefix final_sensitivity
```
