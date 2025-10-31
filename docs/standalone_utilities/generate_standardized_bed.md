# BED Standardization Tool

`generate_standardized_bed.py` is a Python script that reformats BED files in BED6+4 format to a 4-column BED file with standardized feature names. It primarily accepts BED files converted from GTF files using `bedops gtf2bed` as input; thus, the BED6+4 input file should have the following columns:

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

## Motivation

Standardized file formats and consistent naming conventions are essential to the the development, maintenance, and continuous validation of clinical assays. These facilitate clear, version-controlled definitions of assay targets and/or regions, thereby ensuring reproducibility. Furthermore, utilizing a uniform naming structure enables tracability between assay stages, reducing ambiguity and preventing errors.

On a related note, the absence of a standard transcript reference set in the clinical community has complicated variant classification and interpretation. To address this, Ensembl/GENCODE and RefSeq have jointly developed two sets of transcripts, collectively referred to as the [Matched Annotation from NCBI and EMBL-EBI (MANE) transcript sets](https://www.nature.com/articles/s41586-022-04558-8). This includes the MANE Select transcript set, which consists of a single primary transcript per gene, and the MANE Plus Clinical set, which includes additional transcripts to ensure clinically relevant variants are represented.

Since its introduction, the MANE transcript resources have been widely adopted in the clinical community. As such, the `generate_standardized_bed.py` script was primarily designed to take BED files derived from the MANE GTF/GFF files as input and output a standardized BED file of target regions which can be utilized in downstream applications. A detailed protocol for this is outlined below.

## Target BED Generation Procedure

### Getting Started

The following are required for target BED generation:

- Files:
  - MANE GTF/GFF file
    - **Note:** It is recommended to use the MANE Ensembl/Refseq GTF files due to issues encountered when converting GFF files with `bedops gff2bed`
  - File with a list of target gene symbols, one per line
- Tools:
  - `bedops` (tested with `2.4.41--h4ac6f70_2`)
    - **Note:** For reproducibility and cross-platform compatibility, we recommend using the `bedops` container image available from [quay.io](https://quay.io/repository/biocontainers/bedops)

The latest release of the MANE GTF, which contains both MANE Select and MANE Plus Clinical transcripts, can be downloaded from [NCBI's FTP site](https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/). For example, to download the latest release at the time of writing (v1.4):

```
wget https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/MANE.GRCh38.v1.4.refseq_genomic.gtf.gz
```

The `bedops` container image is available on [quay.io](https://quay.io/repository/biocontainers/bedops) and can be pulled using Apptainer:

```
apptainer pull docker://quay.io/biocontainers/bedops:<TAG>
```

### Steps to Generate Target BED

#### Convert MANE GTF to BED6+4 format

Given that the MANE transcript set is in GTF format, the first step is to convert this into BED6+4 format using [`bedops gtf2bed`](https://bedops.readthedocs.io/en/latest/content/reference/file-management/conversion/gtf2bed.html). The attribute from which `bedops` will extract the gene symbol can be specified using `--attribute-key`. Depending on the file, this may not be required:

- Ensembl GTF: `--attribute-key=gene_name`
- RefSeq GTF: `--attribute-key=gene_id` (default, does not need to be specified)

```
apptainer exec -B <HOST_PATH> <BEDOPS_SIF_PATH> gtf2bed [--attribute-key=gene_name] <MANE_GTF>
```

Example output is shown below:

```
chr20	50958817	50963929	MOCS3	.	+	BestRefSeq	exon	.	gene_id "MOCS3"; transcript_id "NM_014484.5"; db_xref "Ensembl:ENST00000244051.3"; db_xref "GeneID:27304"; db_xref "GenBank:NM_014484.5"; db_xref "HGNC:HGNC:15765"; db_xref "MIM:609277"; gene "MOCS3"; product "molybdenum cofactor synthesis 3"; tag "MANE Select"; transcript_biotype "mRNA"; exon_number "1";
```

#### Generate target BED file

Once converted, features for genes of interest can be extracted by filtering on the fourth column, which contains the gene symbol. Furthermore, certain features can be retained/omitted by filtering on the eigth column. While this can be done using various methods, an example to extract exon features for genes of interest using `awk` is shown below:

```
awk 'NR==FNR{genes[$1]++; next} $8 == "exon" && $4 in genes' <TARGET_GENES_FILE> <MANE_BED> > <TARGET_BED>
```

#### Standardize target BED file

Following this, the `generate_bed_script.py` script can be used to standardize the BED file.

```
python generate_standardized_bed.py --bed-file <TARGET_BED> --gene-list <TARGET_GENES_FILE> --output-folder <OUTPUT_DIRECTORY>
```

If intron features are of interest, users may enable the calculation and output of introns in the standardized BED with `--output-introns`:

```
python generate_standardized_bed.py --bed-file <TARGET_BED> --gene-list <TARGET_GENES_FILE> --output-folder <OUTPUT_DIRECTORY> --output-introns
```

That's it! The standardized BED file should look something like this:

```
chr20	50958817	50963929	MOCS3_NM_014484.5_EXON1
```

## Troubleshooting

**Missing genes in target BED file**

- If genes are missing, check to see whether the gene symbol is present in the original MANE **RefSeq** GTF file
- In some instances, the gene symbol appears in the `gene_synonym` attribute rather than `gene_id` or `gene_name`
- One example is `L2HGA`:
  ```
  chr14	BestRefSeq	gene	50242434	50312229	.	-	.	gene_id "L2HGDH"; transcript_id ""; db_xref "GeneID:79944"; db_xref "HGNC:HGNC:20499"; db_xref "MIM:609584"; description "L-2-hydroxyglutarate dehydrogenase"; gbkey "Gene"; gene "L2HGDH"; gene_biotype "protein_coding"; gene_synonym "C14orf160"; gene_synonym "L2HGA";
  ```
- If this is the case, add the corresponding symbol stored in the `gene_id` or `gene_name` attribute into the `<TARGET_GENES_FILE>` and re-generate the target BED file using this updated list as input
