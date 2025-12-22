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


def _extract_exon_number(feature_name: str) -> str:
    """Extract exon number from feature name."""
    feature_name_search = re.search(r"(\d+)$", feature_name)
    if not feature_name_search:
        raise ValueError(
            f"Exon number expected, but none were found in feature name: "
            f"'{feature_name}'"
        )

    return feature_name_search.group(1)


def test_exclude_utrs_and_unpadded_names(test_data_dir: Path) -> None:
    """Test default behaviour - UTRs are excluded, names are not zero-padded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "features_lt100.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"

        subprocess.run(
            [
                "generate-standardized-bed",
                "--bed-file",
                str(input_bed_file),
                "--output-folder",
                str(output_prefix),
            ],
            check=True,
        )

        output_file = output_prefix / "features_lt100.reformatted.bed"
        assert output_file.exists()

        # Extract start and stop coordinates for first and last coding exons, then check
        # coordinates align with start/stop codons
        leftmost_coding_exon_expected = (17, ("chr1", "36466356", "36466827"))
        rightmost_coding_exon_expected = (3, ("chr1", "36479432", "36479496"))
        found_leftmost_exon = False
        found_rightmost_exon = False

        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
                fields = line.strip().split("\t")
                chrom = fields[0]
                start = fields[1]
                end = fields[2]
                feature_name = fields[3]

                exon_number = _extract_exon_number(feature_name)

                # Extract ending digits and ensure exactly two (no padding)
                expected_num_digits = len(str(int(exon_number)))
                assert len(exon_number) == expected_num_digits, (
                    f"Exon number '{exon_number}' in '{feature_name}' should "
                    f"not be zero-padded."
                )

                # Check that exons outside of coding region are excluded
                assert (
                    rightmost_coding_exon_expected[0]
                    <= int(exon_number)
                    <= leftmost_coding_exon_expected[0]
                ), f"EXON{exon_number} in '{feature_name}' is outside coding region."

                # If exon_number corresponds to first or last coding exon, check
                # coordinates align with start/stop codons
                if "EXON" in feature_name:
                    exon_num = int(exon_number)
                    expected_coords = None
                    if exon_num == leftmost_coding_exon_expected[0]:
                        found_leftmost_exon = True
                        expected_coords = leftmost_coding_exon_expected[1]
                    elif exon_num == rightmost_coding_exon_expected[0]:
                        found_rightmost_exon = True
                        expected_coords = rightmost_coding_exon_expected[1]

                    if expected_coords:
                        assert (chrom, start, end) == expected_coords, (
                            f"Exon {exon_number} coordinates ({chrom}, {start}, {end}) "
                            f"don't match expected {expected_coords}"
                        )

        # Ensure test fails if leftmost and rightmost exons are not found
        assert found_leftmost_exon, (
            f"Expected leftmost coding exon (EXON{leftmost_coding_exon_expected[0]}) "
            f"was not found in the output file"
        )
        assert found_rightmost_exon, (
            f"Expected rightmost coding exon (EXON{rightmost_coding_exon_expected[0]}) "
            f"was not found in the output file"
        )


@pytest.mark.parametrize(
    "bed_filename, expected_digits",
    [
        ("features_lt10.bed", 1),
        ("features_lt100.bed", 2),
        ("features_lt1000.bed", 3),
    ],
)
def test_zeropad_name(
    test_data_dir: Path, bed_filename: str, expected_digits: int
) -> None:
    """Test renaming of BED features with zero-padding as needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Filter for exon features only - sufficient to check padding for one feature
        exons_only_bed_filename = bed_filename.replace("features_", "exons_")
        input_bed_file = Path(tmpdir) / exons_only_bed_filename

        with (
            open(test_data_dir / bed_filename, "r") as all_features_bed,
            open(input_bed_file, "w") as exons_bed,
        ):
            for line in all_features_bed:
                fields = line.strip().split("\t")
                if fields[8] == "exon":
                    exons_bed.write(line)
        output_prefix = Path(tmpdir) / "generate_standardized_bed"

        subprocess.run(
            [
                "generate-standardized-bed",
                "--bed-file",
                str(input_bed_file),
                "--output-folder",
                str(output_prefix),
                "--zero-pad-names",
            ],
            check=True,
        )

        output_file = output_prefix / exons_only_bed_filename.replace(
            ".bed", ".reformatted.bed"
        )
        assert output_file.exists()

        # Extract ending digits from each line and check it matches expected number
        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
                fields = line.strip().split("\t")
                feature_name = fields[3]

                exon_number = _extract_exon_number(feature_name)

                assert len(exon_number) == expected_digits, (
                    f"Exon number '{exon_number}' in '{feature_name}' should be "
                    f"{expected_digits}"
                )


def test_include_utrs(test_data_dir: Path) -> None:
    """Test inclusion of UTRs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "features_lt10.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"

        subprocess.run(
            [
                "generate-standardized-bed",
                "--bed-file",
                str(input_bed_file),
                "--output-folder",
                str(output_prefix),
                "--include-utrs",
            ],
            check=True,
        )

        output_file = output_prefix / "features_lt10.reformatted.bed"
        assert output_file.exists()

        # Check that chr, start, and stop coordinates match input - no change
        with open(input_bed_file) as input_bed, open(output_file) as reformatted_bed:
            for input_line, reformatted_line in zip(input_bed, reformatted_bed):
                input_coords = input_line.split("\t")[:3]
                reformatted_coords = reformatted_line.split("\t")[:3]
                assert input_coords == reformatted_coords, (
                    f"All coordinates should not change when UTRs are included; "
                    f"however, a mismatch was detected - Expected {input_coords}, "
                    f"but got {reformatted_coords}."
                )


def test_extend_cds_to_stop(test_data_dir: Path) -> None:
    """Test inclusion of UTRs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "features_lt10.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"

        subprocess.run(
            [
                "generate-standardized-bed",
                "--bed-file",
                str(input_bed_file),
                "--output-folder",
                str(output_prefix),
                "--extend-cds-to-stop",
            ],
            check=True,
        )

        output_file = output_prefix / "features_lt10.reformatted.bed"
        assert output_file.exists()

        # Verify that output file only contains only NRAS features
        leftmost_cds_expected = (5, ("chr1", "114708534", "114708654"))
        found_expected_cds = False

        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
                fields = line.strip().split("\t")
                chrom = fields[0]
                start = fields[1]
                end = fields[2]
                feature_name = fields[3]

                # If exon_number corresponds to CDS adjacent to stop codon, check
                # start/end coordinate matches expected (i.e. aligns stop codon)
                if "CDS" in feature_name:
                    exon_number = int(_extract_exon_number(feature_name))

                    if exon_number == leftmost_cds_expected[0]:
                        found_expected_cds = True
                        expected_coords = leftmost_cds_expected[1]
                        assert (chrom, start, end) == expected_coords, (
                            f"CDS {exon_number} coordinates ({chrom}, {start}, {end}) "
                            f"don't match expected {expected_coords}"
                        )

        # Ensure test fails if CDS adjacent to stop codon is not found
        assert found_expected_cds, (
            f"Expected CDS with exon number {leftmost_cds_expected[0]} was not found "
            f"in the output file"
        )


def test_filter_genes(test_data_dir: Path) -> None:
    """Test behavior with a gene list, including genes absent from BED file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Find all test data files
        feature_bed_files = test_data_dir.glob("features_*.bed")

        # Concatenate files such that multiple genes are present
        input_bed_file = Path(tmpdir) / "features_concatenated.bed"
        with open(input_bed_file, "w") as concatenated_bed:
            for bed_file in feature_bed_files:
                with open(bed_file, "r") as feature_bed:
                    concatenated_bed.write(feature_bed.read())

        output_prefix = Path(tmpdir) / "generate_standardized_bed"

        # Create temporary gene list file
        input_gene_list = Path(tmpdir) / "genes.txt"
        input_gene_list.write_text("\n".join(["NRAS", "ANKRD26"]))

        result = subprocess.run(
            [
                "generate-standardized-bed",
                "--bed-file",
                str(input_bed_file),
                "--output-folder",
                str(output_prefix),
                "--gene-list",
                str(input_gene_list),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        output_file = output_prefix / "features_concatenated.reformatted.bed"
        assert output_file.exists()

        # Verify that output file only contains only NRAS features
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


def test_output_introns_single_exon(test_data_dir: Path) -> None:
    """Test that no introns are generated for single-exon genes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "single_exon.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"

        subprocess.run(
            [
                "generate-standardized-bed",
                "--bed-file",
                str(input_bed_file),
                "--output-folder",
                str(output_prefix),
                "--output-introns",
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
        input_bed_file = test_data_dir / "features_lt10.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"

        subprocess.run(
            [
                "generate-standardized-bed",
                "--bed-file",
                str(input_bed_file),
                "--output-folder",
                str(output_prefix),
                "--output-introns",
            ],
            check=True,
        )

        output_file = output_prefix / "features_lt10.reformatted.bed"
        assert output_file.exists()

        introns = {}
        exons = {}
        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
                fields = line.strip().split("\t")
                start = int(fields[1])
                end = int(fields[2])
                feature_name = fields[3]

                exon_number = _extract_exon_number(feature_name)

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
            assert introns[i][1] == exons[i][0], (
                f"Intron {i} ends at {introns[i][1]}, but exon {i} starts at "
                f"{exons[i][0]}"
            )


def test_exclude_utrs_with_introns(test_data_dir: Path) -> None:
    """Test that introns are correctly generated when UTRs are excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_bed_file = test_data_dir / "features_lt10.bed"
        output_prefix = Path(tmpdir) / "generate_standardized_bed"

        subprocess.run(
            [
                "generate-standardized-bed",
                "--bed-file",
                str(input_bed_file),
                "--output-folder",
                str(output_prefix),
                "--output-introns",
            ],
            check=True,
        )

        output_file = output_prefix / "features_lt10.reformatted.bed"
        assert output_file.exists()

        leftmost_coding_exon = 5
        rightmost_coding_exon = 2

        intron_count = 0
        exon_count = 0

        with open(output_file) as reformatted_bed:
            for line in reformatted_bed:
                fields = line.strip().split("\t")
                feature_name = fields[3]

                exon_number = int(_extract_exon_number(feature_name))

                if "INTRON" in feature_name:
                    assert (
                        rightmost_coding_exon <= exon_number < leftmost_coding_exon
                    ), (
                        f"Intron {exon_number} is outside coding exon range "
                        f"[{rightmost_coding_exon}, {leftmost_coding_exon})"
                    )
                    intron_count += 1
                elif "EXON" in feature_name:
                    exon_count += 1

        # Check that intron count is correct
        assert intron_count == exon_count - 1, (
            f"Expected {exon_count - 1} introns for {exon_count} coding exons, "
            f"got {intron_count}"
        )
