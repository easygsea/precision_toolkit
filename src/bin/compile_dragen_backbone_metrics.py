#!/usr/bin/env python3
"""
Parse DRAGEN output files to compile backbone-level metrics specified in JSON config.

Usage:
    compile-backbone-metrics --metrics-json-config <json_config>
    --analysis-dir <dragen_backbone_analysis_dir> --sample <rgsm_id>
    --output-folder <output_folder>
"""

import argparse
import ast
import csv
import json
import logging
import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@dataclass
class DragenMetric:
    """
    Class representing a DRAGEN metric and its properties.

    Attributes:
        metric_group: Top-level metric group (e.g. "MAPPING/ALIGNING SUMMARY").
        name: Metric name (e.g. "MAPPED_READS").
        mapping_spec: Specification for extracting the metric from source file.
        default_val: Default value to use if metric is missing.
        scale_factor: Factor to scale the metric value by.
        scale_factor_op: Operation to apply with the scale factor (e.g., add, multiply
            divide, subtract).
        num_decimal_places: Number of decimal places metric value should have.
        unit: Unit of measurement for the metric.
        fail_threshold: Threshold value for metric to be considered failing.
        fail_direction: Direction relative to threshold for metric value to be
            considered failing.
        other_properties: Dictionary mapping additional properties to corresponding
            values.
    """

    metric_group: str
    name: str
    mapping_spec: dict
    default_val: float | None
    scale_factor: float | None
    scale_factor_op: str
    num_decimal_places: int | None
    unit: str
    fail_threshold: float | None
    fail_direction: str
    other_properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceFile:
    """
    Class representing a DRAGEN source file and its associated metrics.

    Attributes:
        filename: Path to the source file.
        filetype: Type of the source file (e.g., CSV, JSON).
        allow_missing: If True, source file can be missing and associated metrics will
            use default values.
        default_val: Default value to use if the source file or any metrics are
            missing.
        dragen_metrics: Dictionary mapping metric names to DragenMetric objects.
        reported_metric_names: Set of metric names to be reported.
    """

    filename: str
    filetype: str
    allow_missing: bool
    default_val: float | None
    dragen_metrics: dict[str, DragenMetric]
    reported_metric_names: set[str]


# Valid operations to apply with scale factors
OPERATIONS = {
    "add": operator.add,
    "multiply": operator.mul,
    "divide": operator.truediv,
    "subtract": operator.sub,
    "greater_than": operator.gt,
    "less_than": operator.lt,
}


class DragenMetricsParser:
    """Parser for extracting metrics from DRAGEN analysis output files."""

    def __init__(self, config_path: Path, analysis_dir: str, sample_id: str):
        """
        Initialize parser for DRAGEN output files.

        Args:
            config_path: Path to JSON configuration specifying source files and metrics.
            analysis_dir: Path to directory with DRAGEN analysis results used to replace
                placeholders in config.
            sample_id: Sample ID used to replace placeholders in config.
        """
        # Replace all instances of <DRAGEN_ANALYSIS_DIR> and <SAMPLE_ID>
        with open(config_path, "r") as f:
            content = f.read()
            content = content.replace("<DRAGEN_ANALYSIS_DIR>", analysis_dir)
            content = content.replace("<SAMPLE_ID>", sample_id)

        # Initialize parser with modified JSON content
        source_to_config = json.loads(content).get("DataSources", {})
        self.metric_group_to_sourcefile = self._build_metric_group_sources(
            source_to_config
        )
        self.metric_to_metric_obj = self._build_metric_lookup()

    def _split_metric_property(self, metric_property: str) -> tuple[str, str]:
        """
        Split metric property into metric and attribute.

        Versioned attributes (e.g. MEDIAN_INSERT_SIZE.V1.LSL) are split such that metric
        does not include version info (e.g. ("MEDIAN_INSERT_SIZE", "V1.LSL")).
        """
        property_parts = metric_property.rsplit(".", 2)
        if len(property_parts) == 3:
            # Check if the second part is a version (e.g. V1, V2, etc.)
            if property_parts[1].startswith("V") and property_parts[1][1:].isdigit():
                metric_name = property_parts[0]
                attribute = f"{property_parts[1]}.{property_parts[2]}"
                return metric_name, attribute

        property_parts = metric_property.rsplit(".", 1)
        return property_parts[0], (
            property_parts[1] if len(property_parts) == 2 else ""
        )

    def _get_metric_properties(
        self,
        metric_name: str,
        all_metric_properties: dict[str, float | str],
        all_factor_operations: dict[str, str],
    ) -> tuple[float | None, str, int | None, str, float | None, str, dict[str, Any]]:
        """
        Get properties for all metrics in a source file.

        Properties includes key-value pairs stored under 'Constants', 'Failures', and
        'FactorOperations' in JSON spec.

        Args:
            metric_name: Metric name (e.g. "MAPPED_READS").
            all_metric_properties: Dictionary mapping metric properties to
                value (i.e. 'Constants' and 'Failures' section).
            all_factor_operations: Dictionary mapping metric factor (e.g.
                "<dragen_metric>.FACTOR") to operation (i.e. 'FactorOperations'
                section).

        Raises:
            ValueError: When factor operation is not specified for a metric with a
                scale factor.

        Returns:
            Tuple containing:
                - scale_factor: Factor to scale the metric value by.
                - scale_factor_op: Operation to apply with the scale factor.
                - num_decimal_places: Number of decimal places metric value should have.
                - unit: Unit of measurement for the metric.
                - fail_threshold: Threshold value for metric to be considered failing.
                - fail_direction: Direction relative to threshold for metric value to be
                    considered failing.
                - other_properties: Dictionary mapping additional properties to
                    corresponding values.
        """
        # Set default values
        scale_factor, scale_factor_op = None, ""
        num_decimal_places = None
        unit = "NA"
        fail_threshold, fail_direction = None, ""
        other_properties: dict[str, Any] = {}

        other_properties = {}
        for property, val in all_metric_properties.items():
            metric, attribute = self._split_metric_property(property)
            if metric == metric_name:
                if attribute == "FACTOR":
                    scale_factor = float(val)
                    # Grab operation (required)
                    if property not in all_factor_operations.keys():
                        raise ValueError(
                            f"Factor operation not specified for {metric_name}."
                        )
                    else:
                        scale_factor_op = all_factor_operations[property]
                elif attribute == "RAD":
                    num_decimal_places = int(val)
                elif attribute == "UOM":
                    unit = str(val)
                elif attribute == "THRESHOLD":
                    fail_threshold = float(val)
                elif attribute == "DIRECTION":
                    fail_direction = str(val)
                else:
                    other_properties[attribute] = val
        return (
            scale_factor,
            scale_factor_op,
            num_decimal_places,
            unit,
            fail_threshold,
            fail_direction,
            other_properties,
        )

    def _build_metric_group_sources(
        self, source_to_config: dict[str, Any]
    ) -> dict[str, SourceFile]:
        """
        Create SourceFile objects for each metric group.

        For each 'DataSource' in JSON spec, create SourceFile object by extracting
        metrics, specification for extracting metrics, and properties for each metric.
        """
        metric_group_to_sourcefile = {}
        for metric_group, config in source_to_config.items():
            # Prepare source file attributes
            filename = config.get("SourceName")
            filetype = config.get("SourceType")
            allow_missing = config.get("AllowSourceFileToBeMissing")
            default_val = config.get("DefaultValueOnMissing")

            # Validate that default value is numeric or null
            if default_val is not None and not isinstance(default_val, (int, float)):
                raise ValueError("DefaultValueOnMissing must be numeric or null.")
            default_val = float(default_val) if default_val is not None else None

            # Get metric configuration
            base_metric_mappings = config.get("Mappings", {})
            reported_metric_properties = config.get("Constants", {}) | config.get(
                "Failures", {}
            )
            factor_property_operations = config.get("FactorOperations", {})

            # Create DragenMetric objects for base metrics (those with mapping specs)
            # and derived metrics (those with properties, but no mapping specs)
            all_metric_mappings = {}
            reported_metric_names = set()  # attribute for SourceFile object
            for metric_name in base_metric_mappings.keys():
                all_metric_mappings[metric_name] = base_metric_mappings[metric_name]
            for property in reported_metric_properties.keys():
                metric_name = self._split_metric_property(property)[0]
                if metric_name not in all_metric_mappings.keys():
                    all_metric_mappings[metric_name] = None
                reported_metric_names.add(metric_name)

            valid_dragen_metrics = {}  # attribute for SourceFile object
            for metric_name, mapping_spec_str in all_metric_mappings.items():
                # Get properties for dragen_metric, if available, then create
                # DragenMetric object
                properties = self._get_metric_properties(
                    metric_name,
                    reported_metric_properties,
                    factor_property_operations,
                )
                mapping_spec_dict = (
                    ast.literal_eval(mapping_spec_str) if mapping_spec_str else {}
                )
                dragen_metric_obj = DragenMetric(
                    metric_group,
                    metric_name,
                    mapping_spec_dict,
                    default_val,
                    *properties,
                )
                valid_dragen_metrics[metric_name] = dragen_metric_obj

            # Create SourceFile object
            metric_group_to_sourcefile[metric_group] = SourceFile(
                filename,
                filetype,
                allow_missing,
                default_val,
                valid_dragen_metrics,
                reported_metric_names,
            )

        return metric_group_to_sourcefile

    def _build_metric_lookup(self) -> dict[str, DragenMetric]:
        """Map metric names to DragenMetric objects for quick lookup."""
        return {
            metric_name: dragen_metric_obj
            for source_file_obj in self.metric_group_to_sourcefile.values()
            for metric_name, dragen_metric_obj in (
                source_file_obj.dragen_metrics.items()
            )
        }

    def get_reported_metrics(self) -> set[str]:
        """Retrieve set of all reported metric names."""
        return {
            metric
            for source_file_obj in self.metric_group_to_sourcefile.values()
            for metric in source_file_obj.reported_metric_names
        }

    def _parse_csv(
        self, source_file_obj: SourceFile
    ) -> dict[str, tuple[str, float | None]]:
        """
        Parse CSV source file for metrics.

        Args:
            source_file_obj: SourceFile object.

        Returns:
            Dictionary mapping metric names to tuples of formatted metric name and
            value.
        """
        source_csv_path = source_file_obj.filename
        name_to_metric_obj = source_file_obj.dragen_metrics

        # Create lookup dictionary from mapping specifications
        metric_lookup = {}
        for dragen_metric_obj in name_to_metric_obj.values():
            metric_name = dragen_metric_obj.name
            spec_dict = dragen_metric_obj.mapping_spec
            if spec_dict:  # skip derived metrics (don't have mapping specs)
                metric_description = spec_dict["Row"][0]
                metric_description_index = spec_dict["Row"][1]
                metric_val_index = spec_dict["Col"][0]
                metric_lookup[(metric_name, metric_val_index)] = (
                    dragen_metric_obj.metric_group,
                    metric_description,
                    metric_description_index,
                )

        # Iterate through CSV
        name_to_parsed_metrics = {}
        with open(source_csv_path, "r") as source_file:
            csv_reader = csv.reader(source_file)
            for row in csv_reader:
                for (metric_name, metric_val_index), (
                    metric_group,
                    metric_description,
                    metric_description_index,
                ) in metric_lookup.items():
                    dragen_metric_obj = name_to_metric_obj[metric_name]
                    if (
                        row[0] == metric_group
                        and row[metric_description_index] == metric_description
                    ):
                        metric_val = row[metric_val_index]
                        if metric_val in ("NA", "None", "nan"):
                            # "Missing" value; replace with default missing value
                            logging.warning(
                                f"DRAGEN returned {metric_val} for {metric_name}. "
                                f"Standardizing missing values and replacing with "
                                f"default missing value: "
                                f"{dragen_metric_obj.default_val}."
                            )
                            formatted_metric_name, formatted_value = (
                                format_missing_metric(dragen_metric_obj)
                            )
                        else:
                            # With missing values handled, all values should be float
                            try:
                                # Cast and apply any necessary formatting
                                metric_val_float = float(metric_val)
                                formatted_metric_name, formatted_value = format_metric(
                                    dragen_metric_obj, metric_val_float
                                )
                            except ValueError:
                                # Invalid value; replace with default missing value
                                logging.warning(
                                    f"Numeric type expected for {metric_name}, "
                                    f"but an invalid value was detected: {metric_val}. "
                                    f"Replacing with default missing value: "
                                    f"{dragen_metric_obj.default_val}."
                                )
                                formatted_metric_name, formatted_value = (
                                    format_missing_metric(dragen_metric_obj)
                                )

                        name_to_parsed_metrics[metric_name] = (
                            formatted_metric_name,
                            formatted_value,
                        )

        return name_to_parsed_metrics

    def parse_metrics(self) -> dict[str, tuple[str, float | None]]:
        """
        Parse metrics from all source files.

        Raises:
            FileNotFoundError: When a required source file is missing.

        Returns:
            Dictionary mapping metric names to formatted metric name and value tuples.
        """
        name_to_parsed_metrics = {}
        for source_file_obj in self.metric_group_to_sourcefile.values():
            if Path(source_file_obj.filename).is_file():
                if source_file_obj.filetype == "CSV":
                    parsed_metrics = self._parse_csv(source_file_obj)
                    name_to_parsed_metrics.update(parsed_metrics)
                elif source_file_obj.filetype == "JSON":
                    # TODO: Implement JSON parsing for <DNASAMPLEID>_contamination.json,
                    # though not output by somatic workflow currently
                    pass
            elif source_file_obj.allow_missing:
                logging.warning(f"Source file {source_file_obj.filename} not found.")
            else:
                raise FileNotFoundError(
                    f"Source file {source_file_obj.filename} not found and is required."
                )

            # Set default values for any metrics missing in source file
            expected_metrics = set(source_file_obj.dragen_metrics.keys())
            missing_metrics = set(expected_metrics) - set(name_to_parsed_metrics.keys())
            for metric_name in missing_metrics:
                dragen_metric_obj = source_file_obj.dragen_metrics[metric_name]
                name_to_parsed_metrics[metric_name] = format_missing_metric(
                    dragen_metric_obj
                )
        return name_to_parsed_metrics


def format_metric(
    dragen_metric_obj: DragenMetric, metric_val: float
) -> tuple[str, float]:
    """
    Format metric value based on properties stored in DragenMetric object.

    Args:
        dragen_metric_obj: DragenMetric object, corresponding to metric value.
        metric_val: Value to format.

    Returns:
        Tuple of metric name with the format <metric> (<unit>) and metric value with
        specified number of decimal places.
    """
    # Get dragen metric properties
    metric_name = dragen_metric_obj.name
    num_decimal_places = dragen_metric_obj.num_decimal_places
    unit = dragen_metric_obj.unit

    # Apply formatting, if applicable
    formatted_metric_name = f"{metric_name} ({unit})"
    formatted_metric_val = metric_val
    if num_decimal_places is not None:
        formatted_metric_val = round(formatted_metric_val, num_decimal_places)

    return formatted_metric_name, formatted_metric_val


def format_missing_metric(dragen_metric_obj: DragenMetric) -> tuple[str, float | None]:
    """
    Format missing metric based on properties stored in DragenMetric object.

    This only requires addition of unit to metric name. Default missing value is used
    as metric value.
    """
    formatted_derived_metric_name = (
        f"{dragen_metric_obj.name} ({dragen_metric_obj.unit})"
    )
    metric_val = dragen_metric_obj.default_val
    return formatted_derived_metric_name, metric_val


def scale_metric(dragen_metric_obj: DragenMetric, metric_val: float) -> float:
    """
    Scale metric value based on properties stored in DragenMetric object.

    Args:
        dragen_metric_obj: DragenMetric object, corresponding to metric value.
        metric_val: Value to scale.

    Returns:
        Transformed metric value after applying scale factor.
    """
    # Get dragen metric properties
    scale_factor = dragen_metric_obj.scale_factor
    scale_factor_op = dragen_metric_obj.scale_factor_op

    scaled_metric_val = metric_val
    if scale_factor is not None:
        scaled_metric_val = OPERATIONS[scale_factor_op](metric_val, scale_factor)
    return scaled_metric_val


def calc_derived_pct_metric(
    dragen_metrics_parser: DragenMetricsParser,
    all_dragen_metrics: dict[str, tuple[str, float | None]],
    derived_metric_name: str,
    base_metric_name: str,
) -> tuple[str, float | None]:
    """
    Calculate derived percentage metric.

    Takes a base metric value and divides it by the number of mapped reads
    ("MAPPED_READS") to get the percentage.

    Args:
        dragen_metrics_parser: DragenMetricsParser object.
        all_dragen_metrics: Dictionary mapping metric names to metric name and value
            tuples.
        derived_metric_name: Name of metric to calculate.
        base_dragen_metric: Name of base metric derived_metric_name is calculated
        from.

    Returns:
        Tuple of formatted metric name and value.
    """
    base_metric_val = all_dragen_metrics[base_metric_name][1]
    mapped_reads_val = all_dragen_metrics["MAPPED_READS"][1]
    derived_metric_obj = dragen_metrics_parser.metric_to_metric_obj[derived_metric_name]

    if not base_metric_val or not mapped_reads_val:
        return format_missing_metric(derived_metric_obj)
    else:
        # Calculate derived metric value
        mapped_reads_metric_obj = dragen_metrics_parser.metric_to_metric_obj[
            "MAPPED_READS"
        ]
        scaled_mapped_reads_val = scale_metric(
            mapped_reads_metric_obj, mapped_reads_val
        )

        derived_metric_val = float(base_metric_val) / float(scaled_mapped_reads_val)
        scaled_derived_metric_val = scale_metric(derived_metric_obj, derived_metric_val)

        return format_metric(derived_metric_obj, scaled_derived_metric_val)


def classify_metric(
    dragen_metrics_parser: DragenMetricsParser,
    metric_name: str,
    metric_val: float | None,
) -> str:
    """
    Classify metric depending on whether value satisfies threshold condition.

    A metric is classified as 'Production' if condition is met, otherwise it's
    classified as 'Monitoring'.

    Args:
        dragen_metrics_parser: DragenMetricsParser object.
        metric_name: Name of metric to classify.
        metric_val: Value of dragen metric.

    Returns:
        String, either 'Production' or 'Monitoring'.
    """
    metric_obj = dragen_metrics_parser.metric_to_metric_obj[metric_name]

    if (
        metric_val
        and metric_obj.fail_threshold
        and OPERATIONS[metric_obj.fail_direction](
            float(metric_val), metric_obj.fail_threshold
        )
    ):
        return "Production"
    else:
        return "Monitoring"


def main() -> None:
    """
    Parse DRAGEN output files and compile backbone metrics.

    Returns:
        None, writes metrics to a TSV file.
    """
    parser = argparse.ArgumentParser(
        "Parse DRAGEN analysis files for a given sample, then compile and format "
        "metrics based on provided specification."
    )
    parser.add_argument(
        "-j",
        "--metrics-json-config",
        help="Path to JSON with source files and formatting attributes for metrics.",
        required=True,
    )
    parser.add_argument(
        "-a",
        "--analysis-dir",
        help="Path to directory with DRAGEN analysis results.",
        required=True,
    )
    parser.add_argument("-s", "--sample", help="Sample ID.", required=True)
    parser.add_argument(
        "-o",
        "--output-folder",
        help="Name of folder to output metrics TSV file.",
        required=True,
    )

    # Parse args
    args = parser.parse_args()
    metrics_json_config_path = Path(args.metrics_json_config)
    analysis_folder = args.analysis_dir
    sample_id = args.sample
    output_folder = Path(args.output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)

    # Parse metrics from DRAGEN output files
    dragen_metrics_parser = DragenMetricsParser(
        metrics_json_config_path, analysis_folder, sample_id
    )
    all_dragen_metrics = dragen_metrics_parser.parse_metrics()

    # Calculate remaining metrics not directly output by DRAGEN
    derived_metric_names = [
        "PCT_CONTAMINATION_EST",
        "PCT_CHIMERIC_READS",
        "PCT_READ_ENRICHMENT",
    ]
    for metric_name in derived_metric_names:
        all_dragen_metrics[metric_name] = calc_derived_pct_metric(
            dragen_metrics_parser,
            all_dragen_metrics,
            metric_name,
            f"{metric_name}_BASE",
        )

    # Filter for reported metrics and write to file
    out_filename = output_folder / f"{sample_id}_MetricsOutput.tsv"
    with open(out_filename, "w") as out_dragen_metrics_tsv:
        # Write header
        out_dragen_metrics_tsv.write(f"Metric (UOM)\t{sample_id}\tCategory\n")
        for metric_name, (
            formatted_metric_name,
            metric_val,
        ) in all_dragen_metrics.items():
            if metric_name in dragen_metrics_parser.get_reported_metrics():
                category = classify_metric(
                    dragen_metrics_parser, metric_name, metric_val
                )
                out_dragen_metrics_tsv.write(
                    f"{formatted_metric_name}\t{metric_val}\t{category}\n"
                )


if __name__ == "__main__":
    main()
