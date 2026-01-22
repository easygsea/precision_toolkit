#!/usr/bin/env python3
"""
Parse DRAGEN output files to compile backbone-level metrics specified in JSON config.

Usage:
    compile-dragen-metrics --metrics-json-config <json_config>
    --analysis-dir <dragen_backbone_analysis_dir> --rgsm <rgsm>
    --output-folder <output_folder>
"""

import argparse
from pathlib import Path

from clinical_tools.dragen.metrics_parser import DragenMetricsParser
from clinical_tools.dragen.utils import (
    calc_derived_pct_metric,
    classify_metric,
    format_metric,
)


def main() -> None:
    """
    Parse DRAGEN output files and compile backbone metrics.

    Returns:
        None, writes metrics to a TSV file.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Parse DRAGEN analysis files for a given sample, then compile and format "
            "metrics based on provided specification."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    parser.add_argument(
        "-r", "--rgsm", help="Read group sample name (RGSM).", required=True
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        help="Name of folder to output metrics TSV file.",
        required=True,
    )

    # Parse args
    args = parser.parse_args()
    metrics_json_config_path = Path(args.metrics_json_config)
    analysis_folder = Path(args.analysis_dir)
    rgsm = args.rgsm
    output_folder = Path(args.output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)

    # Parse valid metrics (specified in JSON config) from DRAGEN output files or replace
    # with default value if not present
    dragen_metrics_parser = DragenMetricsParser(
        metrics_json_config_path, analysis_folder, rgsm
    )
    all_dragen_metrics = dragen_metrics_parser.parse_metrics()

    # Calculate remaining metrics not directly output by DRAGEN, if valid (i.e. in JSON
    # config)
    for metric_name in all_dragen_metrics.keys():
        if metric_name.endswith("_BASE"):
            derived_metric_name = metric_name
            metric_name = metric_name.removesuffix("_BASE")
            all_dragen_metrics[metric_name] = calc_derived_pct_metric(
                dragen_metrics_parser.metric_to_metric_obj,
                all_dragen_metrics,
                metric_name,
                derived_metric_name,
            )

    out_filename = output_folder / f"{rgsm}_MetricsOutput.tsv"
    with open(out_filename, "w") as out_dragen_metrics_tsv:
        # Write header
        out_dragen_metrics_tsv.write(
            f"Metric (UOM)\t{rgsm}\tCategory\tThreshold\tFailureDirection\tStatus\n"
        )

        for metric_name, metric_val in all_dragen_metrics.items():
            # Filter for reported metrics only
            if metric_name in dragen_metrics_parser.reported_metric_names:
                dragen_metric_obj = dragen_metrics_parser.metric_to_metric_obj[
                    metric_name
                ]

                # Format metric names (append unit) and values (appropriate number of
                # decimal places)
                if metric_val:
                    formatted_metrics = format_metric(dragen_metric_obj, metric_val)
                else:
                    formatted_metrics = (
                        f"{metric_name} ({dragen_metric_obj.unit})",
                        str(metric_val),
                    )

                # Classify metric as either 'Monitoring' or 'Production' and if
                # 'Production', PASS/FAIL based on threshold
                category, status = classify_metric(dragen_metric_obj, metric_val)

                out_dragen_metrics_tsv.write(
                    f"{formatted_metrics[0]}\t{formatted_metrics[1]}\t{category}"
                    f"\t{dragen_metric_obj.fail_threshold}\t"
                    f"{dragen_metric_obj.fail_direction or 'None'}\t{status}\n"
                )


if __name__ == "__main__":
    main()
