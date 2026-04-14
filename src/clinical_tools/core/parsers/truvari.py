"""Parser for Truvari output."""

import json
import logging
from collections.abc import Sequence
from pathlib import Path

from clinical_tools.core.metrics.variant import VariantCallMetrics


class TruvariDataParser:
    """Parser for Truvari output."""

    @staticmethod
    def process_truvari_output(
        file_path: Path | str,
    ) -> Sequence[VariantCallMetrics]:
        """Process the Truvari output files to extract metrics information.

        Args:
            file_path: Path to the summary.json output file.

        Returns:
            Sequence of VariantCallMetrics objects containing processed data.

        Raises:
            FileNotFoundError: When params.json is not found in the same directory as
                file_path.
        """
        # Derive path to params.json which truvari outputs alongside summary.json
        params_file_path = Path(file_path).parent / Path(file_path).name.replace(
            "refine.variant_summary.json", "params.json"
        ).replace("summary.json", "params.json")
        if not params_file_path.exists():
            raise FileNotFoundError(
                f"{params_file_path} not found. Ensure params.json is present in the "
                f"same directory as {file_path}. "
            )

        # Get VariantCallFilter from params.json
        try:
            with open(params_file_path, "r") as params_file:
                params_data = json.load(params_file)
                variant_filter = "PASS" if params_data["passonly"] else "ALL"

        except Exception as e:
            logging.error(f"Failed to process file {params_file_path}: {str(e)}")
            raise

        # Parse summary.json to get remaining metrics
        try:
            with open(file_path, "r") as summary_file:
                summary_data = json.load(summary_file)

            try:
                metrics = VariantCallMetrics(
                    VariantType="SV",  # Truvari doesn't output stats per type
                    VariantCallFilter=variant_filter,
                    TruthTotal=summary_data["TP-base"] + summary_data["FN"],
                    TruthTP=summary_data["TP-base"],
                    TruthFN=summary_data["FN"],
                    QueryTotal=summary_data["TP-comp"] + summary_data["FP"],
                    QueryTP=summary_data["TP-comp"],
                    QueryFP=summary_data["FP"],
                )

            except Exception as e:
                logging.warning(f"Error processing stats: {str(e)}")

            logging.info("Successfully processed metrics")
            return [metrics]

        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {str(e)}")
            raise
