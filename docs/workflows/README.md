# Workflows

Each workflow has its own dedicated manual describing its usage and parameters. Refer to the corresponding `.md` files for details.

- [Signal Correlation](./signal_correlation.md)
- [Target Evaluation](./target_evaluation.md)
- [Variant Benchmark](./variant_benchmark.md)

#### General Workflow Parameters

Below are a suite of parameters common to all workflows.

- `--workflows`: Use this parameter to select which workflow to run (**_at least one required_**). Multiple workflows can be specified with a comma delimiter.
- `--output_dir`: Directory or path in which to output results (default = "output_clinical_tools"). If specified directory does not exist, it will be created locally or at the path specified.
- `--genome_ref`: Provide reference genome when indicated by workflow docs (eg. for CRAM file expansion; default = null).
- `--decimals`: Number of decimal places (default = 2).
- `--color_palette`: Color palette to use for plotting (e.g., 'colorblind', 'tab10', 'bright').
