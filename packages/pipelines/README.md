# Pipelines

This directory contains WDL workflow definitions for NGS data analysis.

## Directory Structure

```
pipelines/
├── README.md
├── fastqc/
│   └── fastqc.wdl
├── bwa_align/
│   └── bwa_align.wdl
└── variant_calling/
    └── variant_calling.wdl
```

## Pipeline Registration

Pipelines are registered in the `pipeline_versions` table with:
- `name`: Pipeline identifier (e.g., "fastqc")
- `version`: Semantic version (e.g., "1.0.0")
- `wdl_path`: Path to the WDL file
- `is_active`: Whether this version can accept new tasks

## Execution

Pipelines are executed via miniwdl in Celery workers.
Each execution creates a run directory under `/data/pipeline_runs/{task_id}/`.
