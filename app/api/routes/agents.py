"""
app/api/routes/agents.py
─────────────────────────
Agent status endpoint:
  GET /agent-status/{task_id}  — poll task progress (authenticated)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.agents.crew import get_task_status
from app.dependencies import require_auth
from app.middleware.rate_limiter import limiter
from app.models.tasks import AgentStatusResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Agents"])


@router.get(
    "/agent-status/{task_id}",
    response_model=AgentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll the status of a running or completed task",
)
@limiter.limit("30/minute")
async def agent_status(
    request: Request,
    task_id: str,
    user_id: str = Depends(require_auth),
) -> AgentStatusResponse:
    """
    Returns the current state of a task submitted via `/run-task`.

    Possible statuses:
    - `queued`    — task is waiting to start
    - `running`   — agents are actively working
    - `completed` — agents finished; check the `result` field
    - `failed`    — something went wrong; check the `error` field

    **Authentication required** — include `Authorization: Bearer <token>`.
    Users can only view their own tasks.
    """
    record = get_task_status(task_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    # Enforce ownership — users cannot see other users' tasks
    if record.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return AgentStatusResponse(
        task_id=record["task_id"],
        status=record["status"],
        description=record.get("description"),
        result=record.get("result"),
        error=record.get("error"),
        created_at=record.get("created_at"),
        completed_at=record.get("completed_at"),
        agent_type=record.get("agent_type"),
        agent_label=record.get("agent_label"),
    )
