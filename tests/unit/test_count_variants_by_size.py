"""Test count variants by size."""

from pathlib import Path

import pytest

from precision_toolkit.analysis.vcf import count_variants_by_size


@pytest.fixture
def test_vcf(tmp_path: Path) -> str:
    """VCF file with variants of different sizes."""
    vcf_path = tmp_path / "test.vcf"
    with open(vcf_path, "w") as f:
        f.write("##fileformat=VCFv4.2\n")
        f.write("##contig=<ID=1,length=1000000>\n")
        f.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
        f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n")
        f.write("1\t100\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n")  # SNV
        f.write("1\t200\t.\tA\tAT\t.\tPASS\t.\tGT\t0/1\n")  # 1bp insertion
        f.write("1\t300\t.\tAT\tA\t.\tPASS\t.\tGT\t0/1\n")  # 1bp deletion
        f.write("1\t400\t.\tA\tATGC\t.\tPASS\t.\tGT\t0/1\n")  # 3bp insertion
        f.write("1\t500\t.\tATGC\tA\t.\tPASS\t.\tGT\t0/1\n")  # 3bp deletion
        f.write("1\t600\t.\tA\tATGCATGC\t.\tPASS\t.\tGT\t0/1\n")  # 7bp insertion
    return str(vcf_path)


@pytest.fixture
def test_multi_sample_vcf(tmp_path: Path) -> str:
    """Multi-sample VCF file with variants of different sizes."""
    vcf_path = tmp_path / "test.vcf"
    with open(vcf_path, "w") as f:
        f.write("##fileformat=VCFv4.2\n")
        f.write("##contig=<ID=1,length=1000000>\n")
        f.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
        f.write(
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1\tSAMPLE2\n"
        )
        f.write("1\t100\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t0/1\n")  # SNV, 2 occurrences
        f.write(
            "1\t200\t.\tA\tAT\t.\tPASS\t.\tGT\t0/1\t0/0\n"
        )  # 1bp insertion, 1 occurrence
    return str(vcf_path)


@pytest.fixture
def test_multi_sample_vcf_with_end(tmp_path: Path) -> str:
    """Multi-sample VCF file with variants of different sizes and INFO END."""
    vcf_path = tmp_path / "test.vcf"
    with open(vcf_path, "w") as f:
        f.write("##fileformat=VCFv4.2\n")
        f.write("##contig=<ID=1,length=1000000>\n")
        f.write('##INFO=<ID=END,Number=1,Type=Integer,Description="End position">\n')
        f.write('##FORMAT=<ID=CN,Number=1,Type=String,Description="Copy number">\n')
        f.write(
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1\tSAMPLE2\n"
        )
        f.write(
            "1\t100\t.\t.\t<DEL>\t.\tPASS\tEND=200\tCN\t1\t.\n"
        )  # 100bp deletion, 1 occurrence
        f.write(
            "1\t250\t.\t.\t<DUP>\t.\tPASS\tEND=400\tCN\t2.5\t.\n"
        )  # 150bp duplication, 1 occurrence
        f.write(
            "1\t450\t.\t.\t<DEL>\t.\tPASS\tEND=1000\tCN\t0.5\t.\n"
        )  # 550bp deletion, 1 occurrence
        f.write(
            "1\t1050\t.\t.\t<DUP>\t.\tPASS\tEND=2100\tCN\t3\t1.5\n"
        )  # 1050bp duplication, 1 occurrence
    return str(vcf_path)


def test_count_variants_by_size_basic(test_vcf: str) -> None:
    """Test basic counting of variants by size."""
    size_strat = [1, 5]
    expected = {"1": 1, "2-5": 4, ">5": 1}
    result = count_variants_by_size(test_vcf, size_strat)
    assert result == expected


def test_count_variants_by_size_custom_stratification(test_vcf: str) -> None:
    """Test with custom size stratification."""
    size_strat = [1, 3, 10]
    expected = {"1": 1, "2-3": 2, "4-10": 3, ">10": 0}
    result = count_variants_by_size(test_vcf, size_strat)
    assert result == expected


def test_count_variants_by_size_occurrences(test_multi_sample_vcf: str) -> None:
    """Test counting occurrences in multi-sample VCF."""
    size_strat = [1]
    expected = {"1": 2, ">1": 2}
    result = count_variants_by_size(
        test_multi_sample_vcf, size_strat, count_occurrences=True
    )
    assert result == expected


def test_count_variants_by_size_with_end(test_multi_sample_vcf_with_end: str) -> None:
    """Test counting variants by size with END in INFO."""
    size_strat = [100, 500, 1000]
    expected = {"1-100": 0, "101-500": 2, "501-1000": 1, ">1000": 2}
    result = count_variants_by_size(
        test_multi_sample_vcf_with_end, size_strat, count_occurrences=True
    )
    assert result == expected
