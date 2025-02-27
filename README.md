# Clinical Genomics Assay Development & Validation Tools

This software suite streamlines clinical genomics assay development and validation with automated analysis pipelines, result summarization, and report generation. Leveraging containerized environments, it ensures computational reproducibility and cross-platform compatibility across various hardware architectures and high-performance computing systems. By enhancing analytical throughput and maintaining data integrity, it empowers clinical laboratories to enhance efficiency, reliability, and regulatory compliance.

## Supported Architectures

amd64, arm64v8, ppc64le, s390x ([more info](https://github.com/docker-library/official-images#architectures-other-than-amd64))

## Dependencies

- Java (>=17.0.2)
- Nextflow (>=24.10.3)
- Apptainer (>=1.3.1) or Singularity (>=3.8.7)

Containerized dependencies (no installation required): bcftools 1.21 hap.py v0.3.15 htslib 1.21 (bgzip tabix) witty.er 0.5.2.0 Python 3.11.7 samtools 1.21

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/easygsea/clinical_tools.git
   cd clinical_tools
   ```

2. Run specific workflows. Example:
   ```bash
   nextflow run clinical_tools.nf --workflows concordance \
       --truth_dir truth_vcfs/ \
       --query_dir query_vcfs/ \
       --variant_concordance_engine happy \
       --output_dir output_clinical_tools
   ```

Using containerized tools:

1. Clone the repository:
   ```bash
   singularity pull docker://quay.io/easygsea/clinical_tools
   ```

2. Run specific tools. Example:
   ```bash
   singularity exec -B <data_path> /path/to/clinical_tools_latest.sif curate-variant-concordance -h
   ```
   See official [singularity exec](https://docs.sylabs.io/guides/latest/user-guide/cli/singularity_exec.html) manual for guidance on calling commands within a container.

# Contents

- [Motivation](#motivation)
- [Usage](#usage)
  - [Variant Concordance](#variant-concordance)
    - [Variant Concordance Parameters](#variant-concordance-parameters)
    - [Engine Selection Guidelines](#variant-concordance-engine)
    - [Spurious Variant Filtering](#spurious-variant-filtering)
    - [Variant Concordance Output](#variant-concordance-output)
    - [Manual Curation](#variant-concordance-manual-curation)
- [Resource Optimization and High-Performance Computing](#resource-optimization-and-hpc)

## [Motivation](#motivation)

Clinical validation of genomic assays is critical in ensuring the accuracy and reliability of diagnostic tests. However, manual workflows are often time-consuming, error-prone, and difficult to standardize across laboratories, leading to challenges in consistency and reproducibility.

The Clinical Tools software package addresses these challenges with an automated, containerized solution. Built on [Nextflow](https://www.nextflow.io/) with containerized dependencies, it offers a standardized framework that ensures reproducibility and comparability across institutions.

The pipeline's architecture supports execution across various computing environments, from local machines to high-performance computing clusters, making it accessible to laboratories with different computational resources. By automating complex analysis workflows and providing standardized outputs ([CSV](https://en.wikipedia.org/wiki/Comma-separated_values), [Markdown](https://www.markdownguide.org/), and [Word](https://www.microsoft.com/en-us/microsoft-365/word)), this tool aims to improve the efficiency and reliability of clinical validation studies while meeting regulatory requirements for diagnostic test validation.

## [Usage](#usage)

### [Variant Concordance Analysis](#variant-concordance)

The variant concordance module compares variant calls between truth and query VCF files using either [hap.py](https://github.com/Illumina/hap.py) or [witty.er](https://github.com/EBIvariation/witty.er) as the analysis engine.

#### [Variant Concordance Parameters](#variant-concordance-parameters)

**Required Parameters:**
- `--truth_dir`: The directory containing truth VCF files (ground truth). These must be named as <sample>.truth.vcf or <sample>.truth.vcf.gz.
- `--query_dir`: The directory containing query VCF files (the test or experimental dataset). These must be named as <sample>.query.vcf or <sample>.query.vcf.gz.
- `--variant_concordance_engine`: Analysis engine for variant concordance (`happy` or `wittyer`, default: `happy`)

**Optional Parameters:**
- `--genome_ref`: Reference genome FASTA file (required for hap.py)
- `--output_dir`: Base output directory (default: `output_clinical_tools`)
- `--concordance_dir`: Subdirectory for concordance results (default: `concordance`)
- `--happy_options`: Additional options for hap.py analysis
- `--wittyer_options`: Additional options for witty.er analysis
- `--spurious_variants_vcf`: VCF file containing spurious variants to exclude
- `--collapse`: Collapse option for bcftools isec (default: `both` for happy, `id` for wittyer)
- `--skip_raw`: Skip raw analysis (only available when `spurious_variants_vcf` is provided)

**Official Parameter References:**
- [hap.py parameters](https://github.com/Illumina/hap.py/blob/master/doc/happy.md#command-line-options)
- [witty.er parameters](https://github.com/EBIvariation/witty.er/wiki/Configuration-Parameters)


#### [Engine Selection Guidelines](#variant-concordance-engine)

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


#### [Spurious Variant Filtering](#spurious-variant-filtering)

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
1. Raw Variant Concordance: Performs an initial analysis without spurious variant filtering. Use --skip_raw to bypass this step if only curated results are required.
2. Curated Variant Concordance: Conducts a secondary analysis, excluding variants flagged as spurious in the provided VCF.

**Best Practices:**
- Maintain version control of your spurious variant VCF
- Document the source and criteria for spurious variant identification
- Update the VCF based on new findings


### [Variant Concordance Output](#variant-concordance-output)

The pipeline records reports from variant concordance analysis engines and generates summary tables in multiple formats, facilitating streamlined reporting:

**Directory Structure:**

For example, when spurious_variants_vcf is supplied:
```bash
<output_dir>/
    └── <concordance_dir>/
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
        ├── variant_concordance_happy_raw.csv       # Raw concordance in CSV
        ├── variant_concordance_happy_curated.csv   # Curated concordance in CSV
        ├── variant_concordance_happy_combined.md   # Combined raw/curated concordance in Markdown
        └── variant_concordance_happy_combined.docx # Combined raw/curated concordance in Word
```

Example summary in Markdown:
```bash
# Raw Variant Concordance

This table summarizes the raw concordance of variant calls.

| Variant Type   | Variant Filter   |   True Positive |   False Negative |   False Positive | Concordance   | CI Lower   | CI Upper   |
|----------------|------------------|-----------------|------------------|------------------|---------------|------------|------------|
| INDEL          | ALL              |              31 |               15 |               16 | 50.0%         | 37.9%      | 62.1%      |
| INDEL          | PASS             |              31 |               15 |               16 | 50.0%         | 37.9%      | 62.1%      |
| SNP            | ALL              |            1340 |               25 |                0 | 98.2%         | 97.3%      | 98.8%      |
| SNP            | PASS             |            1340 |               25 |                0 | 98.2%         | 97.3%      | 98.8%      |

# Curated Variant Concordance

This table summarizes the concordance of curated variant calls.

| Variant Type   | Variant Filter   |   True Positive |   False Negative |   False Positive | Concordance   | CI Lower   | CI Upper   |
|----------------|------------------|-----------------|------------------|------------------|---------------|------------|------------|
| INDEL          | ALL              |              29 |                0 |                0 | 100.0%        | 88.3%      | 100.0%     |
| INDEL          | PASS             |              29 |                0 |                0 | 100.0%        | 88.3%      | 100.0%     |
| SNP            | ALL              |            1337 |                0 |                0 | 100.0%        | 99.7%      | 100.0%     |
| SNP            | PASS             |            1337 |                0 |                0 | 100.0%        | 99.7%      | 100.0%     |
```

For more defails on hap.py and witty.er outputs:
- [hap.py output documentation](https://github.com/Illumina/hap.py?tab=readme-ov-file#happy)
- [witty.er output documentation](https://github.com/Illumina/witty.er?tab=readme-ov-file#outputs)

#### [Manual Curation](#variant-concordance-manual-curation)

In some cases, manual curation of variant concordance results is necessary, for example, reclassifying a false negative (FN) as a true positive (TP) after investigation. Users can run the curate-variant-concordance script to manually update counts, after which the pipeline will recalculate the curated statistics.

Example usage:
```bash
singularity exec -B <data_path> /path/to/clinical_tools_latest.sif curate-variant-concordance \
--input variant_concordance_happy_curated.csv \
--curation INDEL:PASS:TP:30 --curation INDEL:PASS:TP:30 INDEL:PASS:FP:1 \
--output_prefix variant_concordance_happy_curated_final
```

## [Resource Optimization and High-Performance Computing](#resource-optimization-and-hpc)

The package can be executed across diverse computing environments, from local machines to high-performance computing (HPC) clusters.

### Resource Management

Its workflows implement several resource optimization strategies:

1. **Dynamic Resource Allocation**:
   - Automatically allocates CPU and memory based on task requirements and retry attempts
   - Allocation scaling:
     - Initial attempt: 2 CPUs, 4GB memory
     - Second attempt: 4 CPUs, 8GB memory
     - Third attempt: 6 CPUs, 16GB memory
     - Subsequent attempts: Up to 8 CPUs, 32GB memory

2. **Containerization**:
   - All dependencies are containerized using Docker/Singularity
   - Reduces installation overhead and dependency conflicts

3. **Parallel Execution**:
   - Processes samples in parallel where possible

### HPC Integration

It supports seamless integration with HPC environments:

1. **SLURM Support**:
   - Pre-configured SLURM profile for cluster execution
   - Customizable parameters:
     ```bash
     --slurm_account <account_name>
     --slurm_partition <partition_name>
     --slurm_queue <queue_name>
     ```
   - Automatic job submission and monitoring

2. **Resource Limits**:
   - Configurable maximum resource usage:
     ```bash
     --max_cpus <n>  # Maximum CPUs per task (default: 16)
     --max_memory <size>  # Maximum memory per task (default: 64GB)
     ```

3. **Error Handling**:
   - Automatic retry for common HPC errors:
     - Memory allocation failures
     - Timeout errors
     - Disk quota exceeded
   - Maximum 5 retry attempts per task

### Performance Optimization Tips

1. **Local Execution**:
   ```bash
   nextflow run clinical_tools.nf -profile standard
   ```

2. **Cluster Execution**:
   ```bash
   nextflow run clinical_tools.nf -profile slurm \
       --slurm_account <your_account> \
       --slurm_partition <partition_name>
   ```

3. **Resource Monitoring**:
   - Use Nextflow's built-in monitoring:
     ```bash
     nextflow log <run_id>
     ```
   - View detailed resource usage statistics

For optimal performance, ensure your system meets the minimum requirements and consider these recommendations when configuring your execution environment.
