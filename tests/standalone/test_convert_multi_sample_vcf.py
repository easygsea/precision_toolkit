"""Integration tests for conversion of multi sample VCF files."""

import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest

SAMPLE1_HEADER = [
    "#CHROM",
    "POS",
    "ID",
    "REF",
    "ALT",
    "QUAL",
    "FILTER",
    "INFO",
    "FORMAT",
    "SAMPLE1",
]
SAMPLE2_HEADER = [
    "#CHROM",
    "POS",
    "ID",
    "REF",
    "ALT",
    "QUAL",
    "FILTER",
    "INFO",
    "FORMAT",
    "SAMPLE2",
]

SAMPLE1_DATA = [
    "chr11",
    "118339396",
    ".",
    ".",
    "<DUP>",
    ".",
    "PASS",
    "GENE=ABC;cHGVS=c.0000_0000_ABC;END=00001234",
    "LIBRARY:POOL:CN:GT",
    "F00:AA000:4:1/0",
]
SAMPLE2_DATA = [
    "chr11",
    "118339396",
    ".",
    ".",
    "<DUP>",
    ".",
    "PASS",
    "GENE=ABC;cHGVS=c.0000_0000_DEF;END=56780000",
    "LIBRARY:POOL:CN:GT",
    "F01:AA001:5:1/1",
]


@pytest.fixture
def test_data_dir():
    """Fixture for the test data directory."""
    return Path(__file__).parent / "data"


def test_two_sample_vcf_conversion(test_data_dir):
    """Test conversion of two-sample VCF file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = test_data_dir / "two_sample.vcf"
        output_prefix = Path(tmpdir) / "multi_sample_vcf_conversion"

        subprocess.run(
            [
                "convert-multi-sample-vcf",
                str(input_file),
                "-o",
                str(output_prefix),
                "--suffix",
                "truth",
            ],
            check=True,
        )

        output_sample1 = output_prefix / "SAMPLE1.truth.vcf"
        output_sample2 = output_prefix / "SAMPLE2.truth.vcf"
        assert output_sample1.exists()
        assert output_sample2.exists()

        df_sample1 = pd.read_csv(
            output_sample1, comment="#", sep="\t", header=None, names=SAMPLE1_HEADER
        )
        df_sample2 = pd.read_csv(
            output_sample2, comment="#", sep="\t", header=None, names=SAMPLE2_HEADER
        )
        rows = df_sample1.shape[0]
        assert rows == 1, "Expected one row in sample 1 and sample 2 output"

        sample1_data = df_sample1.iloc[0]
        for idx, header in enumerate(SAMPLE1_HEADER):
            assert str(sample1_data[header]) == SAMPLE1_DATA[idx]

        sample2_data = df_sample2.iloc[0]
        for idx, header in enumerate(SAMPLE2_HEADER):
            assert str(sample2_data[header]) == SAMPLE2_DATA[idx]
