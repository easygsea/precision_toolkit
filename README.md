# Precision Toolkit: Clinical Genomics Assay Development & Validation

**Precision Toolkit** is a containerized toolkit that integrates end-to-end pipelines for assay benchmarking, sequencing quality assessment, DRAGEN output analysis, and routine laboratory operations.

Analytical tasks are parallelized and orchestrated within a continuous integration/continuous deployment (CI/CD) framework that promotes best practices, reduces platform dependencies, and ensures reproducible execution across computational environments.

The toolkit also includes demonstration datasets to support adoption, validation, training, and method development.

## Supported Architectures

amd64, arm64v8, ppc64le, s390x ([more info](https://github.com/docker-library/official-images#architectures-other-than-amd64))

## Dependencies

- Java (>=17.0.2)
- Nextflow (>=25.04.6)
- Apptainer (>=1.3.1)

### Containerized dependencies (no installation required):
> **Note:** These tools are preinstalled in the container and can be used directly outside workflows. No installation required. For tool descriptions and official documentation, see [Containerized Tools](./docs/containerized_tools/README.md).
> **Architecture note:** The current Dockerfile installs precompiled `mafft`, `bedtools`, `bedops`, and `d2` artifacts that are amd64-only.
- bcftools 1.21
- bedops 2.4.41
- bedtools 2.31.0
- d2 0.7.0
- hap.py 0.3.15
- htslib 1.21 (bgzip tabix)
- MAFFT 7.505-1
- Python 3.13.12
- RTG Tools 3.12.1
- samtools 1.21
- Truvari 5.4.0
- uv 0.10.7
- witty.er 0.5.2.0

## Quick Start

1. Clone the repository:

   ```bash
   git clone https://github.com/easygsea/precision_toolkit.git
   ```

2. Run specific workflow(s). Example:
   ```bash
   nextflow run <path/to/precision_toolkit>/main.nf \
       --workflows variant_benchmark \
       --truth_dir <path/to/truth_vcfs/> \
       --query_dir <path/to/query_vcfs/> \
       --variant_benchmark_engine happy \
       --output_dir output_precision_toolkit
   ```

> **Note:**
> Nextflow saves Apptainer images to a `.apptainer` folder in each `work` directory, using extra disk space.
> See [Nextflow docs](https://nextflow.io/docs/latest/container.html).
>
> To avoid this, set a shared cache by exporting before running the workflow:
>
> ```bash
> export NXF_APPTAINER_CACHEDIR="/shared/nextflow_apptainer_cache"
> ```
>
> Or set `apptainer.cacheDir` in `nextflow.config`.
>
> **Advanced users:**
> If you have deployed precision_toolkit using the recommended [deployment and Bamboo plans](deployment/README.md), you do **not** need to manually set up the Apptainer cache.

### Using Containerized Tools

1. Download the container image:

   > **Tip:** If you have already run a workflow with Precision Toolkit, you likely have a cached Apptainer image (see notes above), so you may not need to download it again.

   For the latest version, run:

   ```bash
   apptainer pull docker://quay.io/easygsea/precision_toolkit
   ```

   To get a specific version, use:

   ```bash
   apptainer pull docker://quay.io/easygsea/precision_toolkit:v1.3.1
   ```

2. Run specific tools inside the container. Example:
   ```bash
   apptainer exec -B <data_path> </path/to/precision_toolkit_latest.sif> manual-diagnostic-metric-curation -h
   ```
   See the official [apptainer exec](https://apptainer.org/docs/user/main/cli/apptainer_exec.html) manual for more details on running commands within a container.

### Running Non-Containerized Tools

Some utilities, such as `liftover_sv_vcf.sh`, can be run directly from the source without a container.
For a full list and documentation of available standalone utilities, see the [Standalone Utilities README](docs/standalone_utilities/README.md).

## Demo Data

Precision Toolkit are rigorously tested at both unit and integration levels. Integration tests, covering workflows and standalone utilities, concurrently provide demos:

[Workflows Tests as Demos](./tests/workflow)

Example:
[Variant Benchmark Tests](./tests/workflow/test_variant_benchmark.yml)
Demo of customized benchmarking small variant calls across multiple samples and calculating variant concordance, sensitivity, precision, confidence intervals (Jeffreys method, 99% CI; default: Wilson method, 95% CI), and F1 score reported to 1 (default: 2) decimal place:

```bash
nextflow run <path/to/precision_toolkit>/main.nf \
    --workflows variant_benchmark \
    --variant_benchmark_engine happy \
    --truth_dir <path/to/precision_toolkit>/tests_data/snv_truth_vcfs \
    --query_dir <path/to/precision_toolkit>/tests_data/snv_query_vcfs \
    --genome_ref <path/to/precision_toolkit>/tests_data/genome.fa \
    --ci_method "jeffreys" \
    --ci_level 0.99 \
    --decimals 1 \
    --output_dir tests_variant_benchmark_happy_raw_decimals1
```

[Standalone Utilities Tests as Demos](./tests/standalone)

Example:
[Manual Diagnostic Metric Curation Tests](./tests/standalone/test_manual_diagnostic_metric_curation.py)
Demo of manual sensitivity curation:

```bash
apptainer exec \
    -B <path/to/precision_toolkit> \
    </path/to/precision_toolkit_latest.sif> \
    manual-diagnostic-metric-curation sensitivity \
    --input <path/to/precision_toolkit>/tests/standalone/data/sensitivity.csv \
    --curation "SNP:PASS:TP:100" "SNP:PASS:FN:50" \
    --output-prefix manually_curated_sensitivity
```

# Contents

- [Manual](#manual)
- [Resource Optimization and High-Performance Computing](#resource-optimization-and-high-performance-computing)

## Manual

The manual is detailed in the [docs](./docs/README.md) directory, including:

- [Workflows](./docs/workflows/README.md)
  - [Signal Correlation](./docs/workflows/signal_correlation.md)
  - [Target Evaluation](./docs/workflows/target_evaluation.md)
  - [Variant Benchmark (Diagnostic Metrics - Concordance, Sensitivity, Precision, F1 Score)](./docs/workflows/variant_benchmark.md)
- [Standalone Utilities](./docs/standalone_utilities/README.md)
  - [Compile DRAGEN metrics](./docs/standalone_utilities/README.md#compile-dragen-metrics)
    - `compile-dragen-metrics`
  - [Convert Multi-Sample VCF File into Single-Sample VCF files](./docs/standalone_utilities/README.md#convert-multi-sample-vcf-file-into-single-sample-vcf-files)
    - `convert-multi-sample-vcf`
  - [Count Variants By Size](./docs/standalone_utilities/README.md#count-variants-by-size)
    - `count-variants-by-size`
  - [Generate Standardized BED](./docs/standalone_utilities/README.md#generate-standardized-bed)
    - `generate-standardized-bed`
  - [Jira Table Converter](./docs/standalone_utilities/README.md#jira-table-converter)
    - `jira-table`
  - [Manual Diagnostic Metric Curation](./docs/standalone_utilities/README.md#manual-diagnostic-metric-curation)
    - `manual-diagnostic-metric-curation`
  - [Plot Contamination VAFs](./docs/standalone_utilities/README.md#plot-contamination-vafs)
    - `plot-contamination-vafs`
  - [Plot DRAGEN metrics](./docs/standalone_utilities/README.md#plot-dragen-metrics)
    - `plot-dragen-metrics`
  - [Pull Request Fetcher](./docs/standalone_utilities/README.md#pull-request-fetcher)
    - `fetch-pull-requests`
  - [Structural Variant VCF Liftover](./docs/standalone_utilities/liftover_sv_vcf.md)
    - `liftover_sv_vcf.sh`
- [Containerized Tools](./docs/containerized_tools/README.md)

## Resource Optimization and High-Performance Computing

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
   - Note that the retry pathway only applies to cluster execution
   - For local execution, a maximum time limit of 24 hours is set per task with no retry options

2. **Containerization**:
   - All dependencies are containerized using Docker
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
     --slurm_queue <partition_name>
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
   nextflow run main.nf -profile standard
   ```

2. **Cluster Execution**:
   ```bash
   nextflow run main.nf -profile slurm \
       --slurm_account <your_account> \
       --slurm_queue <partition_name>
   ```

3. **Resource Monitoring**:
   - Use Nextflow's built-in monitoring:
     ```bash
     nextflow log <run_id>
     ```
   - View detailed resource usage statistics

For optimal performance, ensure your system meets the minimum requirements and consider these recommendations when configuring your execution environment.
