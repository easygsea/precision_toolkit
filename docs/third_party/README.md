# Third-Party Tools

This document describes tools that originate from external projects and are adapted for Precision Toolkit.

- [Convert Inversions](#convert-inversions)

## Convert Inversions

- Origin: Manta (Illumina)
- Original source: https://github.com/Illumina/manta/blob/master/src/python/libexec/convertInversion.py
- License context: Header retained in source file
- Precision Toolkit command: `convert-inversions`

`convert-inversions` converts DRAGEN inversion breakend records into symbolic inversion (`<INV>`) records.

Usage:

```bash
convert-inversions <samtools_path> <reference_fasta> <vcf_file>
```

Write bgzip-compressed output and create a tabix index:
```bash
convert-inversions <samtools_path> <reference_fasta> <vcf_file> | bgzip -c > <inversions.vcf.gz>
tabix -p vcf <inversions.vcf.gz>
```

Note: `bgzip` and `tabix` are utilities from htslib, included in the Precision Toolkit container.
