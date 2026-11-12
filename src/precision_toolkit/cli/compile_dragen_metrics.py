"""Parse DRAGEN output files to compile backbone-level metrics specified in JSON config.

Usage:
    compile-dragen-metrics --metrics-json-config <json_config>
    --analysis-dirs <dragen_backbone_analysis_dir> [<dragen_backbone_analysis_dir> ...]
    --rgsm <rgsm> --output-folder <output_folder> [--section-name <name>]
"""

import argparse
from pathlib import Path

from precision_toolkit.dragen.metrics_parser import DragenMetricsParser
from precision_toolkit.dragen.utils import (
    calc_derived_pct_metric,
    classify_metric,
    format_metric,
)


def main() -> None:
    """Compile DRAGEN backbone metrics and write to TSV."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate a tab-delimited table of DRAGEN metrics for a given sample. "
            "--section-name generates a sectioned TSV with an INI-style header."
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
        "--analysis-dirs",
        nargs="+",
        help="Path(s) to one or more directories with DRAGEN analysis results.",
        required=True,
    )
    parser.add_argument(
        "-r",
        "--rgsm",
        help="Read group sample name (RGSM).",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--section-name",
        default=None,
        help="Write sectioned TSV with an INI-style section header using the supplied "
        "value as the section name. "
        "If omitted, write the default TSV format.",
    )
    parser.add_argument(
        "--no-failure-threshold-fallback",
        action="store_true",
        help="Keep missing sectioned TSV guideline values as NA instead of using "
        "failure thresholds.",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        help="Name of folder to output metrics TSV file.",
        required=True,
    )

    args = parser.parse_args()
    metrics_json_config_path = Path(args.metrics_json_config)
    analysis_folders = [Path(dir) for dir in args.analysis_dirs]
    rgsm = args.rgsm
    section_name = args.section_name
    no_failure_threshold_fallback = args.no_failure_threshold_fallback
    if no_failure_threshold_fallback and not section_name:
        parser.error("--no-failure-threshold-fallback requires --section-name")
    output_folder = Path(args.output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)

    dragen_metrics_parser = DragenMetricsParser(metrics_json_config_path, rgsm)
    all_dragen_metrics = dragen_metrics_parser.parse_metrics(analysis_folders)

    for metric_name in all_dragen_metrics:
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
        if section_name:
            out_dragen_metrics_tsv.write(f"[{section_name}]\n")
            out_dragen_metrics_tsv.write(
                f"Metric (UOM)\tLSL Guideline\tUSL Guideline\t{rgsm}\n"
            )
        else:
            out_dragen_metrics_tsv.write(
                f"Metric (UOM)\tCategory\t{rgsm}\tFailureDirection\tThreshold\tStatus\n"
            )

        for reported_metric_name in dragen_metrics_parser.reported_metric_names:
            dragen_metric_obj = dragen_metrics_parser.metric_to_metric_obj[
                reported_metric_name
            ]
            metric_val = all_dragen_metrics[reported_metric_name]

            formatted_metrics = format_metric(dragen_metric_obj, metric_val)
            metric_label, metric_val_str = formatted_metrics[0], formatted_metrics[1]
            if section_name:
                if no_failure_threshold_fallback:
                    lsl = dragen_metric_obj.configured_lsl
                    usl = dragen_metric_obj.configured_usl
                else:
                    lsl, usl = dragen_metric_obj.lsl, dragen_metric_obj.usl
                _, lsl_str = format_metric(dragen_metric_obj, lsl)
                _, usl_str = format_metric(dragen_metric_obj, usl)
                out_dragen_metrics_tsv.write(
                    f"{metric_label}\t{lsl_str}\t{usl_str}\t{metric_val_str}\n"
                )
            else:
                _, fail_threshold_str = format_metric(
                    dragen_metric_obj, dragen_metric_obj.fail_threshold
                )
                category, status = classify_metric(dragen_metric_obj, metric_val)
                out_dragen_metrics_tsv.write(
                    f"{metric_label}\t{category}\t{metric_val_str}"
                    f"\t{dragen_metric_obj.fail_direction or 'NA'}\t"
                    f"{fail_threshold_str}\t{status}\n"
                )


if __name__ == "__main__":
    main()
