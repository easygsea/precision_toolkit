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
        label: Metric name (e.g. "MAPPED_READS").
        mapping_spec: Specification for extracting the metric from source file.
        default_val: Default value to use if metric is missing.
        scale_factor: Factor to scale the metric value by.
        scale_factor_op: Operation to apply with the scale factor (e.g., add, multiply
            divide, subtract).
        num_decimal_places: Number of decimal places metric value should have.
        unit: Unit of measurement for the metric.
        other_properties: Dictionary mapping additional properties to corresponding
            values.
    """

    metric_group: str
    label: str
    mapping_spec: dict
    default_val: Any
    scale_factor: float | None
    scale_factor_op: str
    num_decimal_places: int | None
    unit: str
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
        reported_dragen_metrics: Set of metric names to be reported.
    """

    filename: str
    filetype: str
    allow_missing: bool
    default_val: Any
    dragen_metrics: dict[str, DragenMetric]
    reported_dragen_metrics: set[str]


# Valid operations to apply with scale factors
OPERATIONS = {
    "add": operator.add,
    "multiply": operator.mul,
    "divide": operator.truediv,
    "subtract": operator.sub,
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

    def _split_metric_property(self, dragen_metric_property: str) -> tuple[str, Any]:
        """
        Split metric property into metric and attribute.

        Versioned attributes (e.g. MEDIAN_INSERT_SIZE.V1.LSL) are split such that metric
        does not include version info (e.g. ("MEDIAN_INSERT_SIZE", "V1.LSL")).
        """
        property_parts = dragen_metric_property.rsplit(".", 2)
        if len(property_parts) == 3:
            # Check if the second part is a version (e.g. V1, V2, etc.)
            if property_parts[1].startswith("V") and property_parts[1][1:].isdigit():
                metric = property_parts[0]
                attribute = f"{property_parts[1]}.{property_parts[2]}"
                return metric, attribute

        property_parts = dragen_metric_property.rsplit(".", 1)
        return property_parts[0], (
            property_parts[1] if len(property_parts) == 2 else None
        )

    def _get_metric_properties(
        self,
        dragen_metric: str,
        all_dragen_metric_properties: dict,
        all_factor_operations: dict,
    ) -> tuple[float | None, str, int | None, str, dict]:
        """
        Get properties for all metrics in a source file.

        Properties includes key-value pairs stored under 'Constants' and
        'FactorOperations' in JSON spec.

        Args:
            dragen_metric: Metric name (e.g. "MAPPED_READS").
            all_dragen_metric_properties: Dictionary mapping metric properties to
                value (i.e. 'Constants' section).
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
                - other_properties: Dictionary mapping additional properties to
                    corresponding values.
        """
        scale_factor, scale_factor_op, num_decimal_places, unit = None, "", None, "NA"
        other_properties = {}
        for property, val in all_dragen_metric_properties.items():
            metric, attribute = self._split_metric_property(property)
            if metric == dragen_metric:
                if attribute == "FACTOR":
                    scale_factor = float(val)
                    # Grab operation (required)
                    if property not in all_factor_operations.keys():
                        raise ValueError(
                            f"Factor operation not specified for {dragen_metric}."
                        )
                    else:
                        scale_factor_op = all_factor_operations[property]
                elif attribute == "RAD":
                    num_decimal_places = int(val)
                elif attribute == "UOM":
                    unit = str(val)
                else:
                    other_properties[attribute] = val
        return (
            scale_factor,
            scale_factor_op,
            num_decimal_places,
            unit,
            other_properties,
        )

    def _build_metric_group_sources(
        self, source_to_config: dict
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

            # Create DragenMetric objects for base metrics (those with mapping specs)
            # and derived metrics (those with properties, but no mapping specs)
            base_metric_mappings = config.get("Mappings", {})
            reported_metric_properties = config.get("Constants", {})
            factor_property_operations = config.get("FactorOperations", {})

            all_metric_mappings = {}
            reported_dragen_metrics = set()
            for dragen_metric in base_metric_mappings.keys():
                all_metric_mappings[dragen_metric] = base_metric_mappings[dragen_metric]
            for property in reported_metric_properties.keys():
                dragen_metric = self._split_metric_property(property)[0]
                if dragen_metric not in all_metric_mappings.keys():
                    all_metric_mappings[dragen_metric] = None
                reported_dragen_metrics.add(dragen_metric)

            valid_dragen_metrics = {}
            for dragen_metric, mapping_spec_str in all_metric_mappings.items():
                # Get properties for dragen_metric, if available, then create
                # DragenMetric object
                factor, factor_op, rad, uom, other_properties = (
                    self._get_metric_properties(
                        dragen_metric,
                        reported_metric_properties,
                        factor_property_operations,
                    )
                )
                mapping_spec_dict = (
                    ast.literal_eval(mapping_spec_str) if mapping_spec_str else {}
                )
                dragen_metric_obj = DragenMetric(
                    metric_group,
                    dragen_metric,
                    mapping_spec_dict,
                    default_val,
                    factor,
                    factor_op,
                    rad,
                    uom,
                    other_properties,
                )
                valid_dragen_metrics[dragen_metric] = dragen_metric_obj

            # Create SourceFile object
            metric_group_to_sourcefile[metric_group] = SourceFile(
                filename,
                filetype,
                allow_missing,
                default_val,
                valid_dragen_metrics,
                reported_dragen_metrics,
            )

        return metric_group_to_sourcefile

    def _build_metric_lookup(self) -> dict[str, DragenMetric]:
        """Map metric names to DragenMetric objects for quick lookup."""
        metric_to_metric_obj = {}
        for source_file_obj in self.metric_group_to_sourcefile.values():
            for (
                dragen_metric,
                dragen_metric_obj,
            ) in source_file_obj.dragen_metrics.items():
                metric_to_metric_obj[dragen_metric] = dragen_metric_obj
        return metric_to_metric_obj

    def get_reported_metrics(self) -> set[str]:
        """Retrieve set of all reported metric names."""
        reported_metrics = set()
        for source_file_obj in self.metric_group_to_sourcefile.values():
            reported_metrics.update(source_file_obj.reported_dragen_metrics)
        return reported_metrics

    def _parse_csv(self, source_file_obj: SourceFile) -> dict[str, tuple[str, str]]:
        """
        Parse CSV source file for metrics.

        Args:
            source_file_obj: SourceFile object.

        Returns:
            Dictionary mapping metric names to tuples of formatted metric label and
            value.
        """
        source_csv_path = source_file_obj.filename
        dragen_metrics = source_file_obj.dragen_metrics

        # Create lookup dictionary from mapping specifications
        dragen_metric_lookup = {}
        for dragen_metric_obj in dragen_metrics.values():
            dragen_metric = dragen_metric_obj.label
            spec_dict = dragen_metric_obj.mapping_spec
            if spec_dict:  # skip derived metrics (don't have mapping specs)
                metric_label = spec_dict["Row"][0]
                metric_label_index = spec_dict["Row"][1]
                metric_val_index = spec_dict["Col"][0]
                dragen_metric_lookup[(dragen_metric, metric_val_index)] = (
                    dragen_metric_obj.metric_group,
                    metric_label,
                    metric_label_index,
                )

        # Iterate through CSV
        parsed_dragen_metrics = {}
        with open(source_csv_path, "r") as source_file:
            csv_reader = csv.reader(source_file)
            for row in csv_reader:
                for (dragen_metric, metric_val_index), (
                    metric_group,
                    metric_label,
                    metric_label_index,
                ) in dragen_metric_lookup.items():
                    if (
                        row[0] == metric_group
                        and row[metric_label_index] == metric_label
                    ):
                        # Apply any necessary formatting
                        formatted_dragen_metric, formatted_value = format_metric(
                            dragen_metrics[dragen_metric], row[metric_val_index]
                        )
                        parsed_dragen_metrics[dragen_metric] = (
                            formatted_dragen_metric,
                            formatted_value,
                        )

        return parsed_dragen_metrics

    def parse_metrics(self) -> dict[str, tuple[str, str]]:
        """
        Parse metrics from all source files.

        Raises:
            FileNotFoundError: When a required source file is missing.

        Returns:
            Dictionary mapping metric names to formatted metric label and value tuples.
        """
        all_parsed_dragen_metrics = {}
        for metric_group, source_file_obj in self.metric_group_to_sourcefile.items():
            if Path(source_file_obj.filename).is_file():
                if source_file_obj.filetype == "CSV":
                    parsed_dragen_metrics = self._parse_csv(source_file_obj)
                    all_parsed_dragen_metrics.update(parsed_dragen_metrics)
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

            # Set default values for any missing metrics
            expected_dragen_metrics = set(source_file_obj.dragen_metrics.keys())
            missing_dragen_metrics = set(expected_dragen_metrics) - set(
                all_parsed_dragen_metrics.keys()
            )
            for dragen_metric in missing_dragen_metrics:
                dragen_metric_obj = source_file_obj.dragen_metrics[dragen_metric]

                # Formatting only required for dragen metric label - add unit, if
                # available
                if dragen_metric_obj.unit:
                    formatted_dragen_metric = (
                        f"{dragen_metric} ({dragen_metric_obj.unit})"
                    )
                else:
                    formatted_dragen_metric = dragen_metric

                all_parsed_dragen_metrics[dragen_metric] = (
                    formatted_dragen_metric,
                    source_file_obj.default_val,
                )

        return all_parsed_dragen_metrics


def format_metric(dragen_metric_obj: DragenMetric, metric_val: Any) -> tuple[str, str]:
    """
    Format metric value based on properties stored in DragenMetric object.

    Args:
        dragen_metric_obj: DragenMetric object, corresponding to metric value.
        metric_val: Value to format.

    Returns:
        Tuple of metric label with the format <metric> (<unit>) and metric value with
        specified number of decimal places.
    """
    # Get dragen metric properties
    metric_label = dragen_metric_obj.label
    num_decimal_places = dragen_metric_obj.num_decimal_places
    unit = dragen_metric_obj.unit

    # Apply formatting, if applicable
    formatted_metric_label = f"{metric_label} ({unit})"
    if metric_val and metric_val != "NA":
        formatted_metric_val = float(metric_val)

        if num_decimal_places is not None:
            formatted_metric_val = round(formatted_metric_val, num_decimal_places)
    else:
        formatted_metric_val = metric_val

    return formatted_metric_label, str(formatted_metric_val)


def scale_metric(dragen_metric_obj: DragenMetric, metric_val: Any) -> str:
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

    scaled_metric_val = float(metric_val)
    if scale_factor is not None:
        scaled_metric_val = OPERATIONS[scale_factor_op](metric_val, scale_factor)
    return str(scaled_metric_val)


def calc_derived_pct_metric(
    dragen_metrics_parser: DragenMetricsParser,
    all_dragen_metrics: dict[str, tuple[str, str]],
    derived_dragen_metric: str,
    base_dragen_metric: str,
) -> tuple[str, str]:
    """
    Calculate derived percentage metric.

    Takes a base metric value and divides it by the number of mapped reads
    ("MAPPED_READS") to get the percentage.

    Args:
        dragen_metrics_parser: DragenMetricsParser object.
        all_dragen_metrics: Dictionary mapping metric names to metric label and value
            tuples.
        derived_dragen_metric: Name of metric to calculate.
        base_dragen_metric: Name of base metric derived_dragen_metric is calculated
        from.

    Returns:
        Tuple of formatted metric label and value.
    """
    base_metric_val_str = all_dragen_metrics[base_dragen_metric][1]
    derived_metric_obj = dragen_metrics_parser.metric_to_metric_obj[
        derived_dragen_metric
    ]

    if not base_metric_val_str or base_metric_val_str == "NA":
        # Missing source file and/or metric, use default value
        scaled_derived_metric_val = dragen_metrics_parser.metric_to_metric_obj[
            derived_dragen_metric
        ].default_val
    else:
        # Calculate derived metric value
        base_metric_val = float(base_metric_val_str)

        mapped_reads_val = float(all_dragen_metrics["MAPPED_READS"][1])
        mapped_reads_metric_obj = dragen_metrics_parser.metric_to_metric_obj[
            "MAPPED_READS"
        ]
        scaled_mapped_reads_val = scale_metric(
            mapped_reads_metric_obj, mapped_reads_val
        )

        derived_metric_val = float(base_metric_val) / float(scaled_mapped_reads_val)
        scaled_derived_metric_val = scale_metric(derived_metric_obj, derived_metric_val)

    return format_metric(derived_metric_obj, scaled_derived_metric_val)


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
    all_dragen_metrics["PCT_CONTAMINATION_EST"] = calc_derived_pct_metric(
        dragen_metrics_parser,
        all_dragen_metrics,
        "PCT_CONTAMINATION_EST",
        "PCT_CONTAMINATION_EST_BASE",
    )

    all_dragen_metrics["PCT_CHIMERIC_READS"] = calc_derived_pct_metric(
        dragen_metrics_parser,
        all_dragen_metrics,
        "PCT_CHIMERIC_READS",
        "PCT_CHIMERIC_READS_BASE",
    )

    all_dragen_metrics["PCT_READ_ENRICHMENT"] = calc_derived_pct_metric(
        dragen_metrics_parser,
        all_dragen_metrics,
        "PCT_READ_ENRICHMENT",
        "PCT_READ_ENRICHMENT_BASE",
    )

    # Filter for reported metrics, then write to file
    reported_dragen_metrics = {
        metric: val
        for metric, val in all_dragen_metrics.items()
        if metric in dragen_metrics_parser.get_reported_metrics()
    }

    out_filename = output_folder / f"{sample_id}_MetricsOutput.tsv"
    with open(out_filename, "w") as out_dragen_metrics_tsv:
        # Write header
        out_dragen_metrics_tsv.write(f"Metric (UOM)\t{sample_id}\n")
        for label, val in reported_dragen_metrics.values():
            out_dragen_metrics_tsv.write(f"{label}\t{val}\n")


if __name__ == "__main__":
    main()
