"""Integration tests for plotting VAFs of germline variants to assess contamination."""

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from clinical_tools.core.io import FileMode, open_file


@pytest.fixture
def test_data_dir(pytestconfig: pytest.Config) -> Path:
    """Test data directory."""
    return pytestconfig.rootpath / "tests_data/contamination"


@pytest.fixture
def expected_checksums(test_data_dir: Path) -> dict:
    """Load expected checksums."""
    with open(test_data_dir / "test_plot_contamination_vafs_checksums.json") as f:
        return json.load(f)


@pytest.fixture
def renamed_variant_calls_vcf(test_data_dir: Path, tmp_path: Path) -> Path:
    """Rename variant calls VCF to use as non-DRAGEN input."""
    variant_calls_vcf = (
        test_data_dir / "NA12878_Coriell_IX13680_F161339.hard-filtered.vcf"
    )
    variant_calls_vcf_renamed = tmp_path / "NA12878_Coriell_IX13680_F161339.vcf"
    shutil.copy2(variant_calls_vcf, variant_calls_vcf_renamed)
    return variant_calls_vcf_renamed


def _compute_md5(path: Path) -> str:
    """Compute MD5, stripping VCF headers for VCF files.

    Processing with bcftools results in addition of the command and date/time to the
    header, which results in non-determinitic outputs; thus, headers are stripped prior
    to calculating.
    """
    if path.suffix == ".vcf" or path.name.endswith(".vcf.gz"):
        with open_file(path, FileMode.READ) as f:
            content = "".join(
                line for line in f.readlines() if not line.startswith("#")
            )
        return hashlib.md5(content.encode()).hexdigest()
    return hashlib.md5(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "variant_calls, additional_args, checksum_json_key",
    [
        ("NA12878_Coriell_IX13680_F161339.tmb.trace.tsv", [], "dragen_tmb_trace"),
        (
            "NA12878_Coriell_IX13680_F161339.hard-filtered.vcf",
            [],
            "dragen_vc",
        ),
        (
            "NA12878_Coriell_IX13680_F161339.hard-filtered.vcf",
            ["--population-variants-vcf", "population_variants.vcf"],
            "vc_with_population_variants",
        ),
    ],
)
def test_plot_contamination_vafs(
    test_data_dir: Path,
    expected_checksums: dict,
    variant_calls: str,
    additional_args: list[str],
    checksum_json_key: str,
) -> None:
    """Test plot generation with DRAGEN outputs and germline variant inference."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_folder = Path(tmpdir) / "plot_contamination_vafs"

        # If --population-variants-vcf or --population-marks-vcf is provided, resolve
        # path
        additional_args_resolved = [
            str(test_data_dir / arg) if arg.endswith(".vcf") else arg
            for arg in additional_args
        ]

        subprocess.run(
            [
                "plot-contamination-vafs",
                "--variant-calls",
                str(test_data_dir / variant_calls),
                "--output-folder",
                str(output_folder),
                *additional_args_resolved,
            ],
            check=True,
        )

        # Check that MD5 checksum matches with expected for each output file, with the
        # exception of *.tbi files
        for filename, expected_md5 in expected_checksums[checksum_json_key].items():
            generated_md5 = _compute_md5(output_folder / filename)
            assert generated_md5 == expected_md5


@pytest.mark.parametrize(
    "variant_calls, additional_args",
    [
        (
            "renamed_variant_calls_vcf",
            [],
        ),
        (
            "NA12878_Coriell_IX13680_F161339.hard-filtered.vcf",
            ["--variant-vcf-af-tag", "FORMAT/VAF"],
        ),
        (
            "NA12878_Coriell_IX13680_F161339.hard-filtered.vcf",
            ["--variant-vcf-af-tag", "SAMPLE/VAF"],
        ),
    ],
)
def test_plot_contamination_vafs_invalid_inputs(
    test_data_dir: Path,
    renamed_variant_calls_vcf: Path,
    variant_calls: str,
    additional_args: list[str],
) -> None:
    """Test that invalid inputs exit with non-zero return code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_folder = Path(tmpdir) / "plot_contamination_vafs"

        resolved_variant_calls = (
            renamed_variant_calls_vcf
            if variant_calls == "renamed_variant_calls_vcf"
            else test_data_dir / variant_calls
        )

        result = subprocess.run(
            [
                "plot-contamination-vafs",
                "--variant-calls",
                str(resolved_variant_calls),
                "--output-folder",
                str(output_folder),
                *additional_args,
            ],
        )
        assert result.returncode != 0
