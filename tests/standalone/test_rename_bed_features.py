"""Integration tests for renaming features in BED files."""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir():
    """Fixture for the test data directory."""
    return Path(__file__).parent / "data"


def create_gene_list(tmp_path, genes):
    """Create a temporary gene list file."""
    gene_file = tmp_path / "genes.txt"
    gene_file.write_text("\n".join(genes))
    return gene_file


def test_rename_exons_lt10(test_data_dir):
    """Test renaming of BED features where zero-padding is not needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "exons_lt10.bed"
        output_prefix = Path(tmpdir) / "rename_bed_features"
        input_gene_list = create_gene_list(Path(tmpdir), ["NRAS"])

        subprocess.run(
            [
                "rename-bed-features",
                "-b",
                str(input_bed_file),
                "-g",
                str(input_gene_list),
                "-o",
                str(output_prefix),
            ],
            check=True,
        )

        output_file = output_prefix / "exons_lt10.renamed.bed"
        assert output_file.exists()

        # Extract ending digits from each line and check they're single digit
        with open(output_file) as renamed_bed:
            for line in renamed_bed:
                fields = line.strip().split("\t")
                feature_name = fields[3]
                feature_name_search = re.search(r"(\d+)$", feature_name)
                assert feature_name_search, (
                    f"1 ending digit expected, but none were found in feature name: "
                    f"{feature_name}"
                )

                exon_number = feature_name_search.group(1)
                assert len(exon_number) == 1, (
                    f"Exon number '{exon_number}' in '{feature_name}' should be 1 "
                    f"digit for < 10 features."
                )


def test_rename_exons_lt100(test_data_dir):
    """Test renaming of BED features where zero-padding to two digits is needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "exons_lt100.bed"
        output_prefix = Path(tmpdir) / "rename_bed_features"
        input_gene_list = create_gene_list(Path(tmpdir), ["CSF3R"])

        subprocess.run(
            [
                "rename-bed-features",
                "-b",
                str(input_bed_file),
                "-g",
                str(input_gene_list),
                "-o",
                str(output_prefix),
            ],
            check=True,
        )

        output_file = output_prefix / "exons_lt100.renamed.bed"
        assert output_file.exists()

        # Extract ending digits from each line and check they're two digits
        with open(output_file) as renamed_bed:
            for line in renamed_bed:
                fields = line.strip().split("\t")
                feature_name = fields[3]
                feature_name_search = re.search(r"(\d+)$", feature_name)
                assert feature_name_search, (
                    f"2 ending digits expected, but none were found in feature name: "
                    f"{feature_name}"
                )

                exon_number = feature_name_search.group(1)
                assert len(exon_number) == 2, (
                    f"Exon number '{exon_number}' in '{feature_name}' should be 2 "
                    f"digits for < 100 features."
                )


def test_bed_with_missing_targets(test_data_dir):
    """Test behavior when gene list contains genes not in BED file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "exons_lt10.bed"
        output_prefix = Path(tmpdir) / "rename_bed_features"
        input_gene_list = create_gene_list(Path(tmpdir), ["NRAS", "ANKRD26"])

        result = subprocess.run(
            [
                "rename-bed-features",
                "-b",
                str(input_bed_file),
                "-g",
                str(input_gene_list),
                "-o",
                str(output_prefix),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        output_file = output_prefix / "exons_lt10.renamed.bed"
        assert output_file.exists()

        # Verify that the output file was created and contains only NRAS features
        with open(output_file) as renamed_bed:
            for line in renamed_bed:
                fields = line.strip().split("\t")
                feature_name = fields[3]
                assert feature_name.startswith("NRAS_"), (
                    f"Unexpected gene feature encountered: {feature_name}. Only "
                    f"features from 'NRAS' should be output."
                )

        # Check that warning is output due to missing target gene
        assert (
            "One or more target genes were not found in input BED file" in result.stderr
        )


def test_features_missing_refseq_accession(test_data_dir):
    """Test behavior when RefSeq accession is missing in BED attributes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "missing_refseq_accession.bed"
        output_prefix = Path(tmpdir) / "rename_bed_features"
        input_gene_list = create_gene_list(Path(tmpdir), ["CSF3R"])

        result = subprocess.run(
            [
                "rename-bed-features",
                "-b",
                str(input_bed_file),
                "-g",
                str(input_gene_list),
                "-o",
                str(output_prefix),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        output_file = output_prefix / "missing_refseq_accession.renamed.bed"
        assert output_file.exists()
        assert output_file.stat().st_size == 0
        assert "RefSeq accession not found" in result.stderr
