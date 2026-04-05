"""
app/api/routes/tasks.py
────────────────────────
FIX B1 + B4:

B1 FIXED: Uses FastAPI BackgroundTasks instead of asyncio.create_task().
B4 FIXED: body.complexity is now passed through to execute_task_background()
  so the model router receives the caller's preference.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.agents.crew import (
    create_task_record,
    execute_task_background,
    create_smart_task_record,
    execute_smart_task_background,
)
from app.dependencies import require_auth
from app.middleware.rate_limiter import limiter
from app.models.tasks import RunTaskRequest, RunTaskResponse, SmartTaskRequest, SmartTaskResponse
from app.utils.logger import get_logger
from app.utils.sanitizer import InputSanitizationError, sanitize_input

logger = get_logger(__name__)
router = APIRouter(tags=["Tasks"])


@router.post(
    "/run-task",
    response_model=RunTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a task to the multi-agent crew",
)
@limiter.limit("10/minute")
async def run_task(
    request: Request,
    body: RunTaskRequest,
    background_tasks: BackgroundTasks,          # FIX B1
    user_id: str = Depends(require_auth),
) -> RunTaskResponse:
    """
    Accepts a natural-language task description and dispatches it to
    the four-agent CrewAI crew (Architect → Analyst → Engineer → Writer).

    The task runs asynchronously in the background.
    Poll `/agent-status/{task_id}` for results.

    **Authentication required** — include `Authorization: Bearer <token>`.
    """
    try:
        clean_task = sanitize_input(body.task, field_name="task")
    except InputSanitizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    try:
        # Create the record synchronously — returns task_id immediately
        task_id = create_task_record(
            task_description=clean_task,
            user_id=user_id,
            complexity=body.complexity,         # FIX B4 — no longer dropped
        )

        # FIX B1: FastAPI runs this in a thread-pool — no asyncio event loop needed
        background_tasks.add_task(
            execute_task_background,
            task_id,
            clean_task,
            body.complexity,
        )

        logger.info("task_accepted", task_id=task_id, user_id=user_id, complexity=body.complexity)
        return RunTaskResponse(
            task_id=task_id,
            status="queued",
            message="Task submitted. Poll /agent-status/{task_id} for results.",
        )
    except Exception:
        logger.exception("task_submission_error", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit task. Please try again.",
        )


@router.post(
    "/smart-task",
    response_model=SmartTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a task to the Smart Router (Head Agent → 20 Specialists)",
)
@limiter.limit("10/minute")
async def smart_task(
    request: Request,
    body: SmartTaskRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_auth),
) -> SmartTaskResponse:
    """
    Submits a task to the Smart Router system.

    Flow:
    1. Head Router Agent classifies the task (or uses provided agent_type)
    2. The matching Specialist Agent executes the task
    3. Poll `/agent-status/{task_id}` every 3s for results

    Optional: pass `agent_type` to skip routing and go directly to a specialist.
    Valid values: business_plan, pitch_deck, market_research, competitor_analysis,
    product_launch, financial_projections, youtube_strategy, blog_newsletter,
    social_media, study_plan, career_planning, research_paper, client_deliverables,
    campaign_strategy, proposal_pricing, life_organization, travel_planning,
    cooking_planning, brainstorm, casual

    **Authentication required** — include `Authorization: Bearer <token>`.
    """
    try:
        clean_task = sanitize_input(body.task, field_name="task")
    except InputSanitizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    try:
        task_id = create_smart_task_record(
            task_description=clean_task,
            user_id=user_id,
            agent_type=body.agent_type,
        )

        background_tasks.add_task(
            execute_smart_task_background,
            task_id,
            clean_task,
            body.agent_type,
        )

        logger.info("smart_task_accepted", task_id=task_id, user_id=user_id, agent_type=body.agent_type)
        return SmartTaskResponse(
            task_id=task_id,
            status="queued",
            message="Smart task submitted. Poll /agent-status/{task_id} for results.",
            agent_type=body.agent_type,
        )
    except Exception:
        logger.exception("smart_task_submission_error", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit smart task. Please try again.",
        )
