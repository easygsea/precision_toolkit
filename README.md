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
   nextflow run main.nf --workflows concordance \
       --truth_dir truth_vcfs/ \
       --query_dir query_vcfs/ \
       --variant_concordance_engine happy \
       --output_dir output_clinical_tools
   ```

Using containerized tools:

1. Clone the repository:
   ```bash
   apptainer pull docker://quay.io/easygsea/clinical_tools
   ```

2. Run specific tools. Example:
   ```bash
   apptainer exec -B <data_path> /path/to/clinical_tools_latest.sif curate-variant-concordance-manually -h
   ```
   See official [singularity exec](https://docs.sylabs.io/guides/latest/user-guide/cli/singularity_exec.html) manual for guidance on calling commands within a container.

# Contents

- [Motivation](#motivation)
- [Manual](#manual)
- [Resource Optimization and High-Performance Computing](#resource-optimization-and-high-performance-computing)

## Motivation

Clinical validation of genomic assays is critical in ensuring the accuracy and reliability of diagnostic tests. However, manual workflows are often time-consuming, error-prone, and difficult to standardize across laboratories, leading to challenges in consistency and reproducibility.

The Clinical Tools software package addresses these challenges with an automated, containerized solution. Built on [Nextflow](https://www.nextflow.io/) with containerized dependencies, it offers a standardized framework that ensures reproducibility and comparability across institutions.

The pipeline's architecture supports execution across various computing environments, from local machines to high-performance computing clusters, making it accessible to laboratories with different computational resources. By automating complex analysis workflows and providing standardized outputs ([CSV](https://en.wikipedia.org/wiki/Comma-separated_values), [Markdown](https://www.markdownguide.org/), and [Word](https://www.microsoft.com/en-us/microsoft-365/word)), this tool aims to improve the efficiency and reliability of clinical validation studies while meeting regulatory requirements for diagnostic test validation.

## Manual

The manual is detailed in the [docs](./docs/README.md) directory, including:

- [Workflows](./docs/README.md#workflows)
  - [Variant Concordance](./docs/workflows/variant_concordance.md)
- [Standalone Utilities](./docs/README.md#standalone-utilities)
  - [Curate Variant Concordance Manually](./docs/standalone_utilities/standalone_utilities.md#curate-variant-concordance-manually)

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
   nextflow run main.nf -profile standard
   ```

2. **Cluster Execution**:
   ```bash
   nextflow run main.nf -profile slurm \
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
