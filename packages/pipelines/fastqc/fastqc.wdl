version 1.0

## FastQC quality control workflow
## Runs FastQC on input FASTQ files to generate QC reports.

workflow FastQC {
    input {
        File fastq_r1
        File? fastq_r2
        String sample_id
    }

    call RunFastQC as qc_r1 {
        input:
            fastq = fastq_r1,
            sample_id = sample_id,
            read = "R1"
    }

    if (defined(fastq_r2)) {
        call RunFastQC as qc_r2 {
            input:
                fastq = select_first([fastq_r2]),
                sample_id = sample_id,
                read = "R2"
        }
    }

    output {
        File qc_report_r1 = qc_r1.report_html
        File? qc_report_r2 = qc_r2.report_html
        File qc_data_r1 = qc_r1.report_zip
        File? qc_data_r2 = qc_r2.report_zip
    }
}

task RunFastQC {
    input {
        File fastq
        String sample_id
        String read
    }

    command <<<
        fastqc ~{fastq} --outdir . --threads 2
    >>>

    output {
        File report_html = glob("*.html")[0]
        File report_zip = glob("*.zip")[0]
    }

    runtime {
        docker: "biocontainers/fastqc:v0.11.9_cv8"
        cpu: 2
        memory: "4G"
    }
}
