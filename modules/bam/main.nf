process INDEX_BAM_FILE {
    tag "${sample_name}"

    input:
    tuple val(sample_name), path(bam_file), val(pool)

    output:
    path OUT, emit: bam_index

    script:
    OUT="${bam_file.baseName}.bai"
    """
    samtools index ${bam_file} -o ${OUT}
    """
}

process GET_PER_BASE_STATS {
    label "dynamic_resource"
    tag "${sample_name}"

    // Current specs used here:
    // 1. Output all positions in bed file
    // 2. Min BQ of 10 consider BQ in calculations (ref old) (TODO: pass in values, with default here, caveat 0 for baseq in docs)
    // 3. Min MQ of 1 (ref old)
    // 4. -A count anomalous reads pairs -x turn off overlaps removal
    // 5. Custom gawk to adjust for deletions & parse

    input:
    path targets_bed
    tuple val(sample_name), path(in_bam), val(pool_id)
    val min_bq_per_read
    val min_mq_per_read

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: parsed_pileup

    script:
    OUT="${in_bam.baseName}.mpileup.per_base.parsed.txt"
    """
    samtools mpileup -A -aa -x --min-BQ 0 --min-MQ 0 --output-MQ \
    --no-output-ends --no-output-ins --no-output-ins --no-output-del --no-output-del \
    --positions ${targets_bed} ${in_bam} |
    gawk -v OFS='\\t' '
    function decode_quality_score(target_chr, low, high, mid) {
        if (low > high) {return -10;}
        mid = int ((low+high)/2);
        if (sprintf("%c",mid) == target_chr) {
            return mid;
        } else if (sprintf("%c",mid) < target_chr) {
            return decode_quality_score(target_chr, mid + 1, high);
        } else {
            return decode_quality_score(target_chr, low, mid - 1);
        }
    }
    BEGIN {
        print "#CHROM","POS","COVERAGE","BASEQ_MED", \
        "BASEQ_Q1","MAPQ_MED","MAPQ_Q1","POOL";
    }
    {
        total_non_del=\$4; del_index = index(\$5, "*");
        while(del_index!=0) {
            total_non_del--;
            \$5=substr(\$5,1,del_index-1)substr(\$5,del_index+1);
            \$6=substr(\$6,1,del_index-1)substr(\$6,del_index+1);
            \$7=substr(\$7,1,del_index-1)substr(\$7,del_index+1);
            del_index = index(\$5, "*");
        }
        baseQ=0; mapQ=0; baseQs[1]=-1; mapQs[1]=-1; baseQ_count=0; mapQ_count=0; coverage=0;
        for(i=1;i<=total_non_del;i++) {
            baseChr=substr(\$6,i,1);
            mapChr=substr(\$7,i,1);
            baseQ=decode_quality_score(baseChr,0,255,127)-33;
            mapQ=decode_quality_score(mapChr,0,255,127)-33;
            if (baseQ >= ${min_bq_per_read.coverage_analysis} && mapQ >= ${min_mq_per_read.coverage_analysis}) {
                coverage++;
            }
            if (baseQ >= ${min_bq_per_read.baseq_analysis} && mapQ >= ${min_mq_per_read.baseq_analysis}) {
                baseQ_count++;
                baseQs[baseQ_count]=baseQ;
            }
            if (baseQ >= ${min_bq_per_read.mapq_analysis} && mapQ >= ${min_mq_per_read.mapq_analysis}) {
                mapQ_count++;
                mapQs[mapQ_count]=mapQ;
            }
        }
        asort(baseQs); asort(mapQs);
        q1_index_baseq=int((baseQ_count+3)/4);
        q1_index_mapq=int((mapQ_count+3)/4);
        if (baseQ_count==0) {q1_index_baseq=1}
        if (mapQ_count==0) {q1_index_mapq=1}
        print(\$1,\$2,coverage,baseQs[q1_index_baseq],mapQs[q1_index_mapq],"${pool_id}")
        delete baseQs; delete mapQs;
    }' - > ${OUT}
    """
}

process GET_PER_BASE_STATS_NO_PARSE {
    label "dynamic_resource"
    tag "${sample_name}"
    publishDir "${params.output_dir}/${params.target_evaluation_subdir}/raw_mpileups", mode: 'copy'

    input:
    path(targets_bed)
    tuple val(sample_name), path(in_bam), val(pool_id)

    output:
    tuple val(sample_name), path(OUT), val(pool_id), emit: raw_mpileup_out

    script:
    OUT="${in_bam.baseName}.mpileup.raw.txt"
    """
    samtools mpileup -A -aa -x --min-BQ 0 --min-MQ 0 --output-MQ \
    --no-output-ends --no-output-ins --no-output-ins --no-output-del --no-output-del \
    --positions ${targets_bed} ${in_bam} > ${OUT}
    """
}
