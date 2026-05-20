"""Pipeline task API routes."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.pipeline.celery_tasks import PipelineTaskRunner
from okbox.apps.pipeline.executor import get_task_log
from okbox.apps.pipeline.task_models import PipelineTask, PipelineVersion, TaskStatus
from okbox.apps.pipeline.task_schemas import (
    TaskListQuery,
    TaskLogResponse,
    TaskResponse,
    TaskSubmitRequest,
)
from okbox.core.database import get_db
from okbox.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def submit_task(
    request: TaskSubmitRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Submit a new pipeline task."""
    # Look up pipeline version
    result = await db.execute(
        select(PipelineVersion).where(
            PipelineVersion.name == request.pipeline_name,
            PipelineVersion.version == request.pipeline_version,
            PipelineVersion.is_active == True,  # noqa: E712
        )
    )
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise ValidationException(
            f"Pipeline '{request.pipeline_name}' version '{request.pipeline_version}' not found"
        )

    # Create task record
    task = PipelineTask(
        pipeline_name=request.pipeline_name,
        pipeline_version=request.pipeline_version,
        wdl_path=pipeline.wdl_path,
        sample_id=request.sample_id,
        inputs=request.inputs,
        parameters=request.parameters,
        max_retries=request.max_retries,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    # Submit to Celery
    celery_task_id = await PipelineTaskRunner.submit_task(
        task_id=str(task.id),
        wdl_path=pipeline.wdl_path,
        inputs=request.inputs,
        parameters=request.parameters,
    )
    task.celery_task_id = celery_task_id
    await db.flush()

    return TaskResponse.model_validate(task)


@router.get("", response_model=dict)
async def list_tasks(
    status: TaskStatus | None = Query(None),
    sample_id: uuid.UUID | None = Query(None),
    pipeline_name: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List pipeline tasks with filters."""
    stmt = select(PipelineTask)
    count_stmt = select(sa_func.count(PipelineTask.id))

    if status:
        stmt = stmt.where(PipelineTask.status == status)
        count_stmt = count_stmt.where(PipelineTask.status == status)
    if sample_id:
        stmt = stmt.where(PipelineTask.sample_id == sample_id)
        count_stmt = count_stmt.where(PipelineTask.sample_id == sample_id)
    if pipeline_name:
        stmt = stmt.where(PipelineTask.pipeline_name == pipeline_name)
        count_stmt = count_stmt.where(PipelineTask.pipeline_name == pipeline_name)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(PipelineTask.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    tasks = list(result.scalars().all())

    return {
        "items": [TaskResponse.model_validate(t) for t in tasks],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Get task details."""
    result = await db.execute(select(PipelineTask).where(PipelineTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task not found")
    return TaskResponse.model_validate(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Cancel a running task."""
    result = await db.execute(select(PipelineTask).where(PipelineTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task not found")

    if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
        raise ValidationException(f"Cannot cancel task in status: {task.status.value}")

    # Cancel via Celery
    if task.celery_task_id:
        await PipelineTaskRunner.cancel_task(task.celery_task_id)

    task.status = TaskStatus.CANCELLED
    task.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Retry a failed task."""
    result = await db.execute(select(PipelineTask).where(PipelineTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task not found")

    if task.status != TaskStatus.FAILED:
        raise ValidationException("Only failed tasks can be retried")

    if task.retry_count >= task.max_retries:
        raise ValidationException("Maximum retry count reached")

    # Reset and resubmit
    task.status = TaskStatus.RETRYING
    task.retry_count += 1
    task.error_message = None
    task.started_at = None
    task.completed_at = None
    await db.flush()

    # Resubmit to Celery
    celery_task_id = await PipelineTaskRunner.submit_task(
        task_id=str(task.id),
        wdl_path=task.wdl_path,
        inputs=task.inputs,
        parameters=task.parameters,
    )
    task.celery_task_id = celery_task_id
    task.status = TaskStatus.PENDING
    await db.flush()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.get("/{task_id}/log", response_model=TaskLogResponse)
async def get_task_log_endpoint(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskLogResponse:
    """Get task execution log."""
    result = await db.execute(select(PipelineTask).where(PipelineTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task not found")

    log_content = get_task_log(str(task_id))

    return TaskLogResponse(
        task_id=task_id,
        log_content=log_content,
        run_dir=task.run_dir,
    )
