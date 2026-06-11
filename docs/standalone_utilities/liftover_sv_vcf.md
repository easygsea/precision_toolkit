# Structural Variant VCF Liftover Tool

The `liftover_sv_vcf.sh` utility is a helper script in Bash that converts structural variant VCF files from one genome assembly to another using the UCSC liftOver tool.
It is designed primarily for structural variants (SVs, CNVs, breakends, imprecise intervals) and is best used when you need to remap variant coordinates between assemblies (e.g., hg19 to hg38).
For SNVs and indels, consider using Picard's LiftoverVcf.

---

## Overview

The tool performs the following steps:
1. Converts VCF coordinates to BED format
2. Runs UCSC liftover utility to convert coordinates
3. Converts the lifted coordinates back to VCF format
4. Preserves all original VCF information (samples, genotypes, etc.)

## Prerequisites

### UCSC liftOver Utility

The script requires the UCSC liftOver binary to be installed and available in your `PATH`.
See official guideline for downloading: https://genome.ucsc.edu/cgi-bin/hgLiftOver

### Chain Files
You'll need appropriate chain files for the coordinate conversion you want to perform. Common chain files can be downloaded from UCSC:

- **hg19 to hg38:** `https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz`
- **hg38 to hg19:** `https://hgdownload.soe.ucsc.edu/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz`

## Usage

### Basic Usage
```bash
<path/to/precision_toolkit/src/bin/>liftover_sv_vcf.sh input.vcf output.vcf chain_file.chain
```

### Keep Temporary Files for Debugging
```bash
<path/to/precision_toolkit/src/bin/>liftover_sv_vcf.sh input.vcf output.vcf chain_file.chain \
    --temp-dir /path/to/temp \
    --keep-temp \
    --verbose
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `input_vcf` | Path to input VCF file | Required |
| `output_vcf` | Path to output VCF file | Required |
| `chain_file` | Path to chain file for coordinate conversion | Required |
| `--temp-dir` | Temporary directory for intermediate files | `./temp_liftover` |
| `--keep-temp` | Keep temporary files after completion | False |
| `-v, --verbose` | Enable verbose logging | False |

## Input Format

The tool accepts standard VCF files (version 4.2) with the following requirements:

- **Coordinate system:** Must match the source genome of the chain file
- **Chromosome names:** Must be consistent with the chain file (e.g., "chr1" vs "1")
- **File format:** Plain text or gzipped VCF files are supported
- **Samples:** Single or multi-sample VCF files are supported

## Output Format

The output VCF file maintains the same structure as the input with updated coordinates:

- **Header:** Preserved from the original VCF
- **Coordinates:** Updated to the target genome assembly
- **Variants:** Only successfully mapped variants are included
- **Sample data:** All genotype and sample information is preserved

## Common Issues and Solutions

### "UCSC liftOver utility not found"
**Solution:** Install the UCSC liftOver utility as described in the Prerequisites section.

### "Chain file not found"
**Solution:** Download the appropriate chain file for your coordinate conversion.

### "Failed to map variants"
**Cause:** Some variants may not have corresponding coordinates in the target genome.
**Solution:** Check the unmapped variants file (if `--keep-temp` is used) to identify problematic variants.

### Chromosome name mismatches
**Cause:** Chain files may use different chromosome naming conventions.
**Solution:** Ensure your VCF chromosome names match the chain file format (e.g., "chr1" vs "1").

## Integration with Workflows

The tool can be integrated into Nextflow workflows:

```groovy
process LIFTOVER_VCF {
    publishDir "${params.output_dir}/liftover", mode: 'copy'

    input:
    path vcf
    path chain

    output:
    path "*.vcf", emit: vcf

    script:
    def prefix = vcf.baseName
    """
    liftover_sv_vcf.sh ${vcf} ${prefix}_lifted.vcf ${chain} --verbose 2>&1 | tee ${prefix}_liftover.log
    """
}
```
