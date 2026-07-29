# Containerized Tools

This document describes the third-party command-line tools packaged in the Precision Toolkit container image.

Tools are preconfigured and can be run directly with `apptainer exec` (or another compatible container runtime). Where possible, each tool entry includes a short description and a link to version-specific upstream documentation.

## Quick usage

```bash
apptainer exec -B <data_path> </path/to/precision_toolkit_latest.sif> <tool> [args...]
```

## Notes

- When running commands that read or write files, ensure relevant host paths are bound so the container can access your data. Refer to Apptainer's documentation on [bind paths](https://apptainer.org/docs/user/main/bind_paths_and_mounts.html#user-defined-bind-paths) for more information.
- If you have already run a workflow with Precision Toolkit you may already have a cached Apptainer image in a `.apptainer` folder under `work/`.

## Architecture-specific notes

- Precision Toolkit images are published for amd64, arm64v8, ppc64le, and s390x.
- When building directly from this repository's Dockerfile, precompiled `mafft`, `bedtools`, `bedops`, and `d2` artifacts are amd64-only.

## Included tools

- `bcftools` (v1.21) -- utilities for VCF/BCF manipulation and querying. https://github.com/samtools/bcftools/blob/1.21/README.md
- `bedops` (v2.4.41) -- high-performance tools for genomic feature arithmetic and set operations. https://github.com/bedops/bedops/blob/v2.4.41/README.md
- `bedtools` (v2.31.0) -- flexible genome arithmetic utilities. https://github.com/arq5x/bedtools2/blob/v2.31.0/README.md
- `d2` (v0.7.0) -- diagram compiler/renderer for `.d2` files. https://github.com/terrastruct/d2/blob/v0.7.0/README.md
- `hap.py` (v0.3.15) -- small variant comparison and benchmarking toolkit. https://github.com/Illumina/hap.py/blob/v0.3.15/README.md
- `htslib` (v1.21) -- low-level C library for high-throughput sequencing data and associated utilities. https://github.com/samtools/htslib/blob/1.21/README.md
- `mafft` (v7.505-1) -- multiple sequence alignment program. https://mafft.cbrc.jp/alignment/software
- `python` (v3.13.12) -- Python interpreter used by many utilities and helper scripts. https://docs.python.org/3.13
- `rtg` (RTG Tools) -- present via the `hap.py` packaging used in the base image; consult the `hap.py` documentation at the same tag: https://github.com/Illumina/hap.py/blob/v0.3.15/README.md
- `samtools` (v1.21) -- SAM/BAM/CRAM processing utilities. https://github.com/samtools/samtools/blob/1.21/README.md
- `truvari` (v5.4.0) -- toolkit for structural variant benchmarking, merging, and annotation. https://github.com/ACEnglish/truvari/blob/v5.4.0/README.md
- `uv` (v0.10.7) -- fast Python package and project manager used internally by the toolkit to provision reproducible environments. https://github.com/astral-sh/uv/blob/0.10.7/README.md
- `witty.er` (v0.5.2) -- structural variant benchmarking tool. https://github.com/Illumina/witty.er/blob/v0.5.2/README.md

## Examples

Render a D2 diagram from a D2 file under `/data` and write the output to the current working directory:

```bash
apptainer exec \
    -B /data \
    -B $(pwd):/output \
    /path/to/precision_toolkit_latest.sif \
    d2 /data/<d2_diagram_file> /output/<output_svg>

# This will produce an SVG file in the current working directory named <output_svg> based on the D2 diagram file <d2_diagram_file> located in /data. To verify this:

$ ls /data
<d2_diagram_file>

$ ls .
<output_svg>
```

Run `bcftools` on a VCF file in the current working directory:

```bash
apptainer exec -B $(pwd) /path/to/precision_toolkit_latest.sif bcftools view <input_vcf> -Oz -o <output_vcf>
```

## Where to go next

- For details and examples of the toolkit workflows and standalone utilities, see the main manual: [docs/README.md](../README.md).
- For behaviour details of a bundled release, consult the upstream links above and run the tool's `--help` inside the container.
