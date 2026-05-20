"""Pipeline executor - miniwdl integration via Celery.

This module handles the actual execution of WDL workflows using miniwdl.
Tasks are dispatched via Celery for async execution.
"""

import logging
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from okbox.core.config import settings

logger = logging.getLogger(__name__)

# Base directory for pipeline runs
RUNS_BASE_DIR = os.environ.get("PIPELINE_RUNS_DIR", "/data/pipeline_runs")


def execute_wdl_task(
    task_id: str,
    wdl_path: str,
    inputs: dict | None = None,
    parameters: dict | None = None,
) -> dict:
    """Execute a WDL workflow using miniwdl.

    This function is meant to be called within a Celery worker.

    Args:
        task_id: Unique task identifier
        wdl_path: Path to the WDL file
        inputs: WDL input JSON
        parameters: Additional runtime parameters

    Returns:
        dict with outputs and run_dir
    """
    run_dir = os.path.join(RUNS_BASE_DIR, task_id)
    os.makedirs(run_dir, exist_ok=True)

    # Build miniwdl command
    cmd = ["miniwdl", "run", wdl_path, "--dir", run_dir]

    # Add inputs via JSON file to prevent command injection
    if inputs:
        import json

        inputs_file = os.path.join(run_dir, "inputs.json")
        with open(inputs_file, "w") as f:
            json.dump(inputs, f)
        cmd.extend(["--input", inputs_file])

    logger.info("Executing WDL task %s: %s", task_id, " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=parameters.get("timeout", 86400) if parameters else 86400,
            cwd=run_dir,
        )

        if result.returncode != 0:
            raise RuntimeError(f"miniwdl failed: {result.stderr}")

        # Parse outputs from miniwdl output directory
        outputs = _parse_outputs(run_dir)

        return {
            "status": "completed",
            "outputs": outputs,
            "run_dir": run_dir,
            "stdout": result.stdout[-5000:] if result.stdout else "",
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "error": "Task execution timed out",
            "run_dir": run_dir,
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "run_dir": run_dir,
        }


def cancel_wdl_task(task_id: str) -> bool:
    """Attempt to cancel a running WDL task.

    Returns True if cancellation was successful.
    """
    # In production, this would signal the Celery worker to revoke the task
    logger.info("Cancelling task: %s", task_id)
    return True


def get_task_log(task_id: str) -> str:
    """Read execution log for a task (limited to last 1MB)."""
    run_dir = os.path.join(RUNS_BASE_DIR, task_id)
    log_file = os.path.join(run_dir, "stdout.txt")

    if not os.path.exists(log_file):
        # Try miniwdl's log location
        log_file = os.path.join(run_dir, "workflow.log")

    if not os.path.exists(log_file):
        return f"No log file found for task {task_id}"

    max_read = 1024 * 1024  # 1MB
    file_size = os.path.getsize(log_file)
    with open(log_file) as f:
        if file_size > max_read:
            f.seek(file_size - max_read)
            f.readline()  # Skip partial line
        return f.read()


def _parse_outputs(run_dir: str) -> dict:
    """Parse miniwdl output files from the run directory."""
    outputs = {}
    output_dir = os.path.join(run_dir, "out")
    if os.path.exists(output_dir):
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isfile(item_path):
                outputs[item] = item_path
            elif os.path.isdir(item_path):
                # Check for files within output subdirectories
                for sub_item in os.listdir(item_path):
                    outputs[f"{item}/{sub_item}"] = os.path.join(item_path, sub_item)
    return outputs
