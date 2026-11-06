#!/bin/bash

set -euo pipefail

VERBOSE=false
KEEP_TEMP=false
TEMP_DIR="./temp_liftover_$$"

log_msg() {
  local level="$1"
  local msg="$2"
  echo "[$level] $(date '+%Y-%m-%d %H:%M:%S') - $msg"
}

show_usage() {
  cat <<EOF
Structural Variant VCF Liftover Tool

Usage: $0 <input.vcf> <output.vcf> <chain_file> [options]

Arguments:
    input.vcf      Path to input VCF file
    output.vcf     Path to output VCF file
    chain_file     Path to chain file for coordinate conversion

Options:
    -t, --temp-dir DIR    Temporary directory (default: ./temp_liftover_$$)
    -k, --keep-temp       Keep temporary files after completion
    -v, --verbose         Enable verbose output
    -h, --help           Show this help message

Examples:
    $0 input.vcf output.vcf hg19ToHg38.over.chain
    $0 input.vcf output.vcf hg19ToHg38.over.chain --verbose --keep-temp
    $0 input.vcf output.vcf hg19ToHg38.over.chain --temp-dir /tmp/liftover

Prerequisites:
    - UCSC liftOver utility must be installed and in PATH
    - Download from: https://genome.ucsc.edu/cgi-bin/hgLiftOver
EOF
}

check_dependencies() {
  if ! command -v liftOver &>/dev/null; then
    log_msg "ERROR" "UCSC liftOver utility not found in PATH"
    log_msg "ERROR" "Please install it from: https://genome.ucsc.edu/cgi-bin/hgLiftOver"
    exit 1
  fi
}

validate_inputs() {
  local input_vcf="$1"
  local chain_file="$2"
  if [[ ! -f "${input_vcf}" ]]; then
    log_msg "ERROR" "Input VCF file not found: ${input_vcf}"
    exit 1
  fi
  if [[ ! -f "${chain_file}" ]]; then
    log_msg "ERROR" "Chain file not found: ${chain_file}"
    exit 1
  fi
}

vcf_to_bed() {
  local input_vcf="$1"
  local output_bed="$2"
  log_msg "INFO" "Converting VCF to BED format (BED4+INFO)..."
  awk -F'\t' 'BEGIN{OFS="\t"}
	/^#/ { next }
	{
		chrom = $1
		pos = $2
		id = $3
		ref = $4
		info = $8
		end = ""
		if (match(info, /END=([0-9]+)/, arr)) {
			end = arr[1]
		} else {
			end = pos + length(ref) - 1
		}
		start = pos - 1
		if (id == "." || id == "") {
			name = chrom ":" pos
		} else {
			name = id
		}
		print chrom, start, end, name, info
	}' "${input_vcf}" >"${output_bed}"
  local variant_count
  variant_count=$(wc -l <"${output_bed}")
  log_msg "INFO" "Created BED file with ${variant_count} variants"
}

run_liftover() {
  local input_bed="$1"
  local chain_file="$2"
  local output_bed="$3"
  local unmapped_bed="$4"
  log_msg "INFO" "Running UCSC liftover with -bedPlus=4..."
  if [[ "${VERBOSE}" == "true" ]]; then
    log_msg "DEBUG" "Command: liftOver -bedPlus=4 ${input_bed} ${chain_file} ${output_bed} ${unmapped_bed}"
  fi
  if liftOver -bedPlus=4 "${input_bed}" "${chain_file}" "${output_bed}" "${unmapped_bed}"; then
    log_msg "INFO" "Liftover completed successfully"
  else
    log_msg "ERROR" "Liftover failed"
    exit 1
  fi
}

bed_to_vcf() {
  local original_vcf="$1"
  local bed_file="$2"
  local output_vcf="$3"
  local chain_file="$4"
  log_msg "INFO" "Converting BED back to VCF format..."
  local temp_header="${TEMP_DIR}/header.tmp"
  local temp_variants="${TEMP_DIR}/variants.tmp"
  local temp_mapping="${TEMP_DIR}/mapping.tmp"
  awk 'FNR==NR { if (/^chain/) target_contig_lengths[$8]=$9; next }
	/^#/ {
		if (/^##contig/) {
			match($0, /ID=([^,>]+)/, contig_match)
			contig = contig_match[1]
			print "##contig=<ID=" contig (contig in target_contig_lengths ? ",length=" target_contig_lengths[contig] : "") ">"
			next
		}
		print
	}' "${chain_file}" "${original_vcf}" >"${temp_header}"
  awk -F'\t' 'BEGIN{OFS="\t"}{
		name = $4
		new_chrom = $1
		new_start = $2
		new_end = $3
		info = $5
		print name, new_chrom, new_start, new_end, info
	}' "${bed_file}" >"${temp_mapping}"
  awk -F'\t' -v mapping_file="${temp_mapping}" 'BEGIN{OFS="\t"}
	BEGIN {
		while ((getline line < mapping_file) > 0) {
			split(line, fields, "\t")
			mapping[fields[1]] = fields[2] "\t" fields[3] "\t" fields[4] "\t" fields[5]
		}
		close(mapping_file)
	}
	/^#/ { next }
	{
		id = $3
		if (id == "." || id == "") {
			name = $1 ":" $2
		} else {
			name = id
		}
		if (name in mapping) {
			split(mapping[name], new_coords, "\t")
			new_chrom = new_coords[1]
			new_start = new_coords[2]
			new_end = new_coords[3]
			new_info = new_coords[4]
			$1 = new_chrom
			$2 = new_start + 1
			if ($8 ~ /END=[0-9]+/) {
				gsub(/END=[0-9]+/, "END=" new_end, $8)
			} else {
				if ($8 == ".") {
					$8 = "END=" new_end
				} else {
					$8 = $8 ";END=" new_end
				}
			}
			for (i = 1; i <= NF; i++) {
				printf "%s", $i
				if (i < NF) printf OFS
			}
			printf "\n"
		} else {
			printf "Variant %s was not mapped\n", name > "/dev/stderr"
		}
	}' "${original_vcf}" >"${temp_variants}"
  cat "${temp_header}" "${temp_variants}" >"${output_vcf}"
  local mapped_count
  mapped_count=$(wc -l <"${temp_variants}")
  log_msg "INFO" "Created VCF with ${mapped_count} successfully lifted variants"
}

report_statistics() {
  local output_bed="$1"
  local unmapped_bed="$2"
  log_msg "INFO" "Generating liftover statistics..."
  if [[ -f "${output_bed}" ]]; then
    local mapped_count
    mapped_count=$(wc -l <"${output_bed}")
    log_msg "INFO" "Successfully mapped: ${mapped_count} variants"
  fi
  if [[ -f "${unmapped_bed}" ]]; then
    local unmapped_count
    unmapped_count=$(wc -l <"${unmapped_bed}")
    if [[ ${unmapped_count} -gt 0 ]]; then
      log_msg "WARN" "Failed to map: ${unmapped_count} variants"
    fi
  fi
}

cleanup() {
  if [[ "${KEEP_TEMP}" == "false" ]] && [[ -d "${TEMP_DIR}" ]]; then
    log_msg "INFO" "Cleaning up temporary files..."
    rm -rf "${TEMP_DIR}"
  elif [[ "${KEEP_TEMP}" == "true" ]]; then
    log_msg "INFO" "Temporary files preserved in: ${TEMP_DIR}"
  fi
}

main() {
  if [[ $# -lt 3 ]]; then
    log_msg "ERROR" "Missing required arguments"
    show_usage
    exit 1
  fi
  local input_vcf="$1"
  local output_vcf="$2"
  local chain_file="$3"
  while [[ $# -gt 0 ]]; do
    case "$1" in
    -h | --help)
      show_usage
      exit 0
      ;;
    -v | --verbose)
      VERBOSE=true
      shift
      ;;
    -k | --keep-temp)
      KEEP_TEMP=true
      shift
      ;;
    -t | --temp-dir)
      TEMP_DIR="$2"
      shift 2
      ;;
    -*)
      log_msg "ERROR" "Unknown option: $1"
      show_usage
      exit 1
      ;;
    *)
      shift
      ;;
    esac
  done
  log_msg "INFO" "Starting VCF liftover process"
  if [[ "${VERBOSE}" == "true" ]]; then
    log_msg "DEBUG" "Input VCF: ${input_vcf}"
    log_msg "DEBUG" "Output VCF: ${output_vcf}"
    log_msg "DEBUG" "Chain file: ${chain_file}"
    log_msg "DEBUG" "Temporary directory: ${TEMP_DIR}"
  fi
  check_dependencies
  validate_inputs "${input_vcf}" "${chain_file}"
  mkdir -p "${TEMP_DIR}"

  local uncompressed_vcf="${TEMP_DIR}/input.vcf"
  if [[ "${input_vcf}" == *.gz ]]; then
    log_msg "INFO" "Unzipping input VCF to temporary file: ${uncompressed_vcf}"
    if command -v zcat &>/dev/null; then
      zcat "${input_vcf}" >"${uncompressed_vcf}"
    elif command -v gunzip &>/dev/null; then
      gunzip -c "${input_vcf}" >"${uncompressed_vcf}"
    else
      log_msg "ERROR" "Cannot process gzipped VCF: zcat or gunzip not found"
      exit 1
    fi
  else
    cp "${input_vcf}" "${uncompressed_vcf}"
  fi

  local input_bed="${TEMP_DIR}/input.bed"
  local output_bed="${TEMP_DIR}/output.bed"
  local unmapped_bed="${TEMP_DIR}/unmapped.bed"
  trap cleanup EXIT
  vcf_to_bed "${uncompressed_vcf}" "${input_bed}"
  run_liftover "${input_bed}" "${chain_file}" "${output_bed}" "${unmapped_bed}"
  bed_to_vcf "${uncompressed_vcf}" "${output_bed}" "${output_vcf}" "${chain_file}"
  report_statistics "${output_bed}" "${unmapped_bed}"
  log_msg "INFO" "Liftover completed successfully. Output: ${output_vcf}"
}

main "$@"
