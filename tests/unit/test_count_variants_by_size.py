"""Test count variants by size."""

import pytest
from clinical_tools.analysis.vcf import count_variants_by_size

@pytest.fixture
def test_vcf(tmp_path):
    """Create a test VCF file with variants of different sizes."""
    vcf_path = tmp_path / "test.vcf"
    with open(vcf_path, "w") as f:
        f.write("##fileformat=VCFv4.2\n")
        f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n")
        f.write("1\t100\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n")  # SNP
        f.write("1\t200\t.\tA\tAT\t.\tPASS\t.\tGT\t0/1\n")  # 1bp insertion
        f.write("1\t300\t.\tAT\tA\t.\tPASS\t.\tGT\t0/1\n")  # 1bp deletion
        f.write("1\t400\t.\tA\tATGC\t.\tPASS\t.\tGT\t0/1\n")  # 3bp insertion
        f.write("1\t500\t.\tATGC\tA\t.\tPASS\t.\tGT\t0/1\n")  # 3bp deletion
        f.write("1\t600\t.\tA\tATGCATGC\t.\tPASS\t.\tGT\t0/1\n")  # 7bp insertion
    return str(vcf_path)

@pytest.fixture
def test_multi_sample_vcf(tmp_path):
    """Create a test multi-sample VCF file with variants of different sizes."""
    vcf_path = tmp_path / "test.vcf"
    with open(vcf_path, "w") as f:
        f.write("##fileformat=VCFv4.2\n")
        f.write(
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1\tSAMPLE2\n"
        )
        f.write("1\t100\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t0/1\n")  # SNP, 2 occurrences
        f.write(
            "1\t200\t.\tA\tAT\t.\tPASS\t.\tGT\t0/1\t0/0\n"
        )  # 1bp insertion, 1 occurrence
    return str(vcf_path)

def test_count_variants_by_size_basic(test_vcf):
    """Test basic counting of variants by size."""
    size_strat = [1, 5]
    expected = {
        "1": 2,  # 1bp variants
        "2-5": 2,  # 3bp variants
        ">5": 1,  # 7bp variant
    }
    result = count_variants_by_size(test_vcf, size_strat)
    assert result == expected

def test_count_variants_by_size_custom_stratification(test_vcf):
    """Test with custom size stratification."""
    size_strat = [1, 3, 10]
    expected = {
        "1": 2,
        "2-3": 2,
        "4-10": 1
    }
    result = count_variants_by_size(test_vcf, size_strat)
    assert result == expected

def test_count_variants_by_size_occurrences(test_multi_sample_vcf):
    """Test counting occurrences in multi-sample VCF."""
    size_strat = [1]
    expected = { "1": 2, ">1": 0 }
    result = count_variants_by_size(
        test_multi_sample_vcf, size_strat, count_occurrences=True
    )
    assert result == expected
