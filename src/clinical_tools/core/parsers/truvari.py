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
        summary_file_path: Path | str, params_file_path: Path | str
    ) -> Sequence[VariantCallMetrics]:
        """
        Process the Truvari output files to extract metrics information.

        Args:
            summary_file_path: Path to the summary.json output file
            params_file_path: Path to the params.json output file

        Returns:
            Sequence of VariantCallMetrics objects containing processed data
        """
        # Get VariantCallFilter from params JSON
        try:
            with open(params_file_path, "r") as params_file:
                params_data = json.load(params_file)
                variant_filter = "PASS" if params_data["passonly"] else "ALL"

        except Exception as e:
            logging.error(f"Failed to process file {params_file_path}: {str(e)}")
            raise

        # Parse VCFs to remaining metrics
        try:
            with open(summary_file_path, "r") as summary_file:
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
            logging.error(f"Failed to process file {summary_file_path}: {str(e)}")
            raise
