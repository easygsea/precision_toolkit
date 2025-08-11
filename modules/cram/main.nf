process CRAM_TO_BAM_WITH_SUBSET {
    label "dynamic_resource"
    //publishDir "${params.output_dir}/target_eval_results", mode: 'copy'

    input:
    tuple path(alignment_file), val(pool)
    path genome_ref
    path sorted_bed
    val cpus

    output:
    tuple path(bam_file), val(pool), emit: cram_bam

    script:
    bam_file="${alignment_file.baseName}.bam"

    """
    #temp files
    INTERSECTING_READS=intersect_reads.txt
    UNSORTED_RETURN_BAM=subset.temp2.bam
    CACHE=cram_cache_temp

    #export cram reference for bedtools
    export CRAM_REFERENCE=${genome_ref}
    export REF_PATH=\$CACHE/%2s/%2s/%s:http://www.ebi.ac.uk/ena/cram/md5/%s
    export REF_CACHE=\$CACHE/%2s/%2s/%s

    #bedtools intersect bam against panel target space to get any intersecting alignments (note, not inclusive)
    bedtools intersect -a ${alignment_file} -b ${sorted_bed} -bed | cut -f4 | cut -f1 -d"/" | sort | uniq > \$INTERSECTING_READS

    #using the read names that had an intersecting alignment, retrieve those alignments along with all their mates,
    #secondary, and supplementary alignments.
    samtools view -@ ${cpus} -T ${genome_ref} -N \$INTERSECTING_READS -o \$UNSORTED_RETURN_BAM ${alignment_file}

    #sort the inclusive intersection bam file
    samtools sort -@ ${cpus} -o ${bam_file} \$UNSORTED_RETURN_BAM
    """
}
