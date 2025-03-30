# Variant Benchmark (Diagnostic Metrics - Concordance, Sensitivity, Precision, F1 Score)

The variant benchmark module compares variant calls between truth and query VCF files using either [hap.py](https://github.com/Illumina/hap.py) or [witty.er](https://github.com/EBIvariation/witty.er), and calculates diagnostic metrics including concordance, sensitivity, precision, and F1 score.

By default, all metrics, and their confidence intervals (CIs) wherever applicable, are calculated.


## Quick Start

Small variant benchmark:
```bash
nextflow run main.nf \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine happy \
--genome_ref <path/to/genome_ref>
```

Large variant benchmark:
```bash
nextflow run main.nf \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine wittyer
```

Small variant benchmark excluding spurious variants:
```bash
nextflow run main.nf \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine happy \
--genome_ref <path/to/genome_ref> \
--spurious_variants_vcf <path/to/spurious_variants_vcf>
```

Large variant benchmark excluding spurious variants:
```bash
nextflow run main.nf \
--truth_dir <path/to/truth_vcf_dir> \
--query_dir <path/to/query_vcf_dir> \
--variant_benchmark_engine wittyer \
--spurious_variants_vcf <path/to/spurious_variants_vcf>
```

Custom small variant benchmark:
```bash
nextflow run main.nf \
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
- `--truth_dir`: The directory containing truth VCF files (ground truth). These must be named as <sample>.truth.vcf or <sample>.truth.vcf.gz.
- `--query_dir`: The directory containing query VCF files (the test or experimental dataset). These must be named as <sample>.query.vcf or <sample>.query.vcf.gz.
- `--variant_benchmark_engine`: Analysis engine for variant benchmark (`happy` or `wittyer`, default: `happy`)
- `--genome_ref`: Required for hap.py: Reference genome FASTA file

**Optional Parameters:**
- `--diagnostic_metrics`: Diagnostic metrics to calculate (default: all metrics: 'concordance sensitivity precision f1_score'). Multiple values must be passed as a quoted space-separated list. F1 score does not have a confidence interval.
- `--output_dir`: Base output directory (default: `output_clinical_tools`)
- `--variant_benchmark_dir`: Subdirectory for variant benchmark results (default: `variant_benchmark`)
- `--happy_options`: Additional options for hap.py analysis
- `--wittyer_options`: Additional options for witty.er analysis
- `--spurious_variants_vcf`: VCF file containing spurious variants to exclude
- `--collapse`: Collapse option for bcftools isec (default: `both` for happy, `id` for wittyer)
- `--skip_raw`: Skip raw analysis (only available when `spurious_variants_vcf` is provided)
- `--concordance_tp`: Method for defining TP in concordance calculation. Available options: `truth` (use truth set's TP count), `query` (use query set's TP count), `min` (use minimum of truth and query TP counts, default)

**Official Parameter References:**
- [hap.py parameters](https://github.com/Illumina/hap.py/blob/master/doc/happy.md#command-line-options)
- [witty.er parameters](https://github.com/EBIvariation/witty.er/wiki/Configuration-Parameters)


### VCF Comparison Engine Selection Guidelines

1. **Use hap.py when:**
   - Your analysis requires strict matching of variant positions and alleles
   - You are working with small variants (SNPs, indels <50bp)
   - Your reference genome is well-defined and available

2. **Use witty.er when:**
   - You are analyzing structural variants or large indels (>50bp)
   - You need faster processing times for complex variant analysis
   - Your variants may have positional uncertainty or require fuzzy matching
   - You need advanced filtering capabilities based on variant size and type
   - Your analysis benefits from cross-type variant comparison
   - You are working with complex genomic regions or repetitive sequences

**Key Differences:**

| Feature            | hap.py                     | witty.er                   |
|--------------------|----------------------------|----------------------------|
| Variant Size       | Small variants (SNPs, indels) | Large variants (SVs, CNVs) |
| Matching Precision | Exact position/allele      | Fuzzy matching             |
| Speed              | Slower for small variants  | Faster for large variants  |
| Scalability        | Medium                     | High                       |
| Filtering          | Basic                      | Advanced by size/type      |
| Reference Genome   | Required                   | Optional                   |
| Best Use Case      | Small variants, precision | Large variants, throughput |


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

For more defails on hap.py and witty.er outputs:
- [hap.py output documentation](https://github.com/Illumina/hap.py?tab=readme-ov-file#happy)
- [witty.er output documentation](https://github.com/Illumina/witty.er?tab=readme-ov-file#outputs)


### Diagnostic Metrics Manual Curation

In some cases, manual curation of variant benchmark results is necessary, for example, reclassifying a false negative (FN) as a true positive (TP) after investigation. Users can run `manual-variant-concordance-curation`, `manual-sensitivity-curation`, or `manual-precision-curation` to manually update counts, after which the pipeline will recalculate the curated statistics.

Example usage:
```bash
apptainer exec -B <data_path> <path/to/clinical_tools_latest.sif> manual-sensitivity-curation \
--input diagnostic_metrics_happy_curated_sensitivity.csv \
--curation "SNP:PASS:TP:100" "SNP:PASS:FN:50" \
--output_prefix final_sensitivity
```
