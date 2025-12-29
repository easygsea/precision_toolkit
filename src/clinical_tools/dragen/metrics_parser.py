"""Parsing logic for metrics derived from DRAGEN outputs files."""

import ast
import csv
import json
import logging
from pathlib import Path
from typing import Any

from clinical_tools.dragen.models import DragenMetric, SourceFile
from clinical_tools.dragen.utils import scale_metric


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
        self.reported_metric_names = json.loads(content).get("ReportedMetrics", [])
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
            ValueError: When only one of fail threshold or fail direction is specified.

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

        # Exclusive OR to check that if fail_threshold is specified, fail_direction must
        # also be set (and vice-versa)
        if (fail_threshold is None) != (not fail_direction):
            raise ValueError(
                f"Only one of fail_threshold and fail_direction is specified for "
                f"{metric_name}, but both values need to be set."
            )

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

            # Validate default value is numeric or null
            if default_val is not None and not isinstance(default_val, (int, float)):
                raise ValueError("DefaultValueOnMissing must be numeric or null.")
            default_val = float(default_val) if default_val is not None else None

            # Get metric configuration
            base_metric_mappings = config.get("Mappings", {})
            metric_properties = config.get("Constants", {}) | config.get("Failures", {})
            factor_property_operations = config.get("FactorOperations", {})

            # Create DragenMetric objects for base metrics (those with mapping specs)
            # and derived metrics (those with properties, but no mapping specs)
            all_metric_mappings = {}
            for metric_name in base_metric_mappings.keys():
                all_metric_mappings[metric_name] = base_metric_mappings[metric_name]
            for property in metric_properties.keys():
                metric_name = self._split_metric_property(property)[0]
                if metric_name not in all_metric_mappings.keys():
                    all_metric_mappings[metric_name] = None

            valid_dragen_metrics = {}  # attribute for SourceFile object
            for metric_name, mapping_spec_str in all_metric_mappings.items():
                # Get properties for dragen_metric, if available, then create
                # DragenMetric object
                properties = self._get_metric_properties(
                    metric_name,
                    metric_properties,
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

    def _parse_csv(self, source_file_obj: SourceFile) -> dict[str, float | None]:
        """
        Parse CSV source file for metrics.

        Args:
            source_file_obj: SourceFile object.

        Returns:
            Dictionary mapping metric names to transformed value after applying scale
            factor.
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

        # Iterate through CSV and check if metric is present in lookup, if so, extract
        metric_name_to_value: dict[str, float | None] = {}
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
                            scaled_value = dragen_metric_obj.default_val
                        else:
                            # With missing values handled, all values should be float
                            try:
                                metric_val_float = float(metric_val)
                                scaled_value = scale_metric(
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
                                scaled_value = dragen_metric_obj.default_val

                        if metric_name in metric_name_to_value.keys():
                            # Rows with the same metric group (first column) and metric
                            # description (third column) are present in DRAGEN output
                            # file
                            logging.warning(
                                f"{metric_name} is extracted from rows with "
                                f"description '{metric_description}', but multiple "
                                f"matching rows were found in {source_csv_path}. Using "
                                f"last occurrence."
                            )
                        metric_name_to_value[metric_name] = scaled_value

        return metric_name_to_value

    def parse_metrics(self) -> dict[str, float | None]:
        """
        Parse metrics from all source files.

        Raises:
            FileNotFoundError: When a required source file is missing.

        Returns:
            Dictionary mapping metric names to values.
        """
        metric_name_to_value = {}
        for source_file_obj in self.metric_group_to_sourcefile.values():
            if Path(source_file_obj.filename).is_file():
                if source_file_obj.filetype == "CSV":
                    parsed_metrics = self._parse_csv(source_file_obj)
                    metric_name_to_value.update(parsed_metrics)
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
            missing_metrics = set(expected_metrics) - set(metric_name_to_value.keys())
            for metric_name in missing_metrics:
                dragen_metric_obj = source_file_obj.dragen_metrics[metric_name]
                metric_name_to_value[metric_name] = dragen_metric_obj.default_val

        return metric_name_to_value
