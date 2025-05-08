include { build_vcf_pair_channels } from '../../modules/utils/main'
include {
    extract_signal
    plot_signal_correlation
} from '../../modules/signal_correlation/main'

workflow signal_correlation_workflow {
    // Build VCF pair channels
    def vcf_pairs = build_vcf_pair_channels(params.truth_dir, params.query_dir)

    // Extract signals
    extracted_signals = extract_signal(params.truth_signal, params.query_signal, vcf_pairs)

    // Combine signals and calculate correlation
    plot_signal_correlation(
        params.truth_signal,
        params.query_signal,
        extracted_signals.truth_signal.collect(),
        extracted_signals.query_signal.collect(),
        params.xlim,
        params.ylim,
        params.show_regression
    )
}
