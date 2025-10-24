"""Integration tests for generating standardized BED files."""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir() -> Path:
    """Fixture for the test data directory."""
    return Path(__file__).parent / "data"


def create_gene_list(tmp_path: Path, genes: list[str]) -> Path:
    """Create a temporary gene list file."""
    gene_file = tmp_path / "genes.txt"
    gene_file.write_text("\n".join(genes))
    return gene_file


def test_rename_exons_lt10(test_data_dir: Path) -> None:
    """Test renaming of BED features where zero-padding is not needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "exons_lt10.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"
        input_gene_list = create_gene_list(Path(tmpdir), ["NRAS"])

        subprocess.run(
            [
                "generate-standardized-bed",
                "-b",
                str(input_bed_file),
                "-g",
                str(input_gene_list),
                "-o",
                str(output_prefix),
            ],
            check=True,
        )

        output_file = output_prefix / "exons_lt10.reformatted.bed"
        assert output_file.exists()

        # Extract ending digits from each line and check they're single digit
        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
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


def test_rename_exons_lt100(test_data_dir: Path) -> None:
    """Test renaming of BED features where zero-padding to two digits is needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "exons_lt100.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"
        input_gene_list = create_gene_list(Path(tmpdir), ["CSF3R"])

        subprocess.run(
            [
                "generate-standardized-bed",
                "-b",
                str(input_bed_file),
                "-g",
                str(input_gene_list),
                "-o",
                str(output_prefix),
            ],
            check=True,
        )

        output_file = output_prefix / "exons_lt100.reformatted.bed"
        assert output_file.exists()

        # Extract ending digits from each line and check they're two digits
        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
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


def test_bed_with_missing_targets(test_data_dir: Path) -> None:
    """Test behavior when gene list contains genes not in BED file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "exons_lt10.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"
        input_gene_list = create_gene_list(Path(tmpdir), ["NRAS", "ANKRD26"])

        result = subprocess.run(
            [
                "generate-standardized-bed",
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

        output_file = output_prefix / "exons_lt10.reformatted.bed"
        assert output_file.exists()

        # Verify that the output file was created and contains only NRAS features
        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
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


def test_features_missing_refseq_accession(test_data_dir: Path) -> None:
    """Test behavior when RefSeq accession is missing in BED attributes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "missing_refseq_accession.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"
        input_gene_list = create_gene_list(Path(tmpdir), ["CSF3R"])

        result = subprocess.run(
            [
                "generate-standardized-bed",
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

        output_file = output_prefix / "missing_refseq_accession.reformatted.bed"
        assert output_file.exists()
        assert output_file.stat().st_size == 0
        assert "RefSeq accession not found" in result.stderr


def test_output_introns_single_exon(test_data_dir: Path) -> None:
    """Test that no introns are generated for single-exon genes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "single_exon.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"
        input_gene_list = create_gene_list(Path(tmpdir), ["MOCS3"])

        subprocess.run(
            [
                "generate-standardized-bed",
                "-b",
                str(input_bed_file),
                "-g",
                str(input_gene_list),
                "-o",
                str(output_prefix),
                "--output_introns",
            ],
            check=True,
        )

        output_file = output_prefix / "single_exon.reformatted.bed"
        assert output_file.exists()

        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
                fields = line.strip().split("\t")
                feature_name = fields[3]
                assert "INTRON" not in feature_name, (
                    f"Introns should not be generated for single-exon genes, but "
                    f"found intron feature: {feature_name}"
                )


def test_output_introns_multiple_exons(test_data_dir: Path) -> None:
    """Test that introns are correctly generated for multi-exon genes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "exons_lt10.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"
        input_gene_list = create_gene_list(Path(tmpdir), ["NRAS"])

        subprocess.run(
            [
                "generate-standardized-bed",
                "-b",
                str(input_bed_file),
                "-g",
                str(input_gene_list),
                "-o",
                str(output_prefix),
                "--output_introns",
            ],
            check=True,
        )

        output_file = output_prefix / "exons_lt10.reformatted.bed"
        assert output_file.exists()

        introns = {}
        exons = {}
        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
                fields = line.strip().split("\t")
                start = int(fields[1])
                end = int(fields[2])
                feature_name = fields[3]
                feature_name_search = re.search(r"(\d+)$", feature_name)
                assert feature_name_search, (
                    f"1 ending digit expected, but none were found in feature name: "
                    f"{feature_name}"
                )

                exon_number = feature_name_search.group(1)
                if "INTRON" in feature_name:
                    introns[exon_number] = (start, end)
                elif "EXON" in feature_name:
                    exons[exon_number] = (start, end)

        # Check that intron count is correct
        assert len(introns) == len(exons) - 1, (
            f"Expected {len(exons) - 1} introns for {len(exons)} exons, got "
            f"{len(introns)}"
        )

        # For each intron, check it's adjacent to the corresponding exon
        for i in introns.keys():
            assert introns[i][1] + 1 == exons[i][0], (
                f"Intron {i} ends at {introns[i][1]}, but exon {i} starts at "
                f"{exons[i][0]}"
            )
