"""
app/models/tasks.py
────────────────────
Pydantic request/response models for task execution endpoints.
"""

from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class RunTaskRequest(BaseModel):
    task: str
    complexity: Optional[Literal["simple", "medium", "complex"]] = None

    @field_validator("task")
    @classmethod
    def task_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Task description cannot be empty.")
        return v


class RunTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class AgentStatusResponse(BaseModel):
    task_id: str
    status: Literal["queued", "running", "completed", "failed"]
    description: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    agent_type: Optional[str] = None
    agent_label: Optional[str] = None


class SmartTaskRequest(BaseModel):
    task: str
    agent_type: Optional[str] = None  # One of AGENT_TYPES in smart_router.py

    @field_validator("task")
    @classmethod
    def task_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Task description cannot be empty.")
        return v


class SmartTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    agent_type: Optional[str] = None
