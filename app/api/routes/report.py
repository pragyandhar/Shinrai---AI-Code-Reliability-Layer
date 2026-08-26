# WHAT DOES THIS FILE DO: GET /report/{task_id} endpoint — fetches full task result from DB by task_id.

# ================== IMPORTS ==================
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.db import get_db, AnalysisTask
# ================== IMPORTS ==================


# =========== VARIABLES : Schema — inline for now, will move to schemas/report.py later ===========
class TaskResponse(BaseModel):
    task_id: str
    status: str
    prompt: str | None
    original_code: str | None
    fixed_code: str | None
    diff: str | None
    documentation: str | None
    repair_attempt: int | None
    reliability_report: Any | None
    security_report: Any | None
    confidence_report: Any | None
    output_state: str | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}
# =========== VARIABLES : Schema — inline for now, will move to schemas/report.py later ===========


router = APIRouter()


# =========== FUNCTION ===========
# ROLE: fetches the full analysis task record by task_id and returns it, or 404 if not found
@router.get("/report/{task_id}", response_model=TaskResponse)
def get_report(task_id: str, db: Session = Depends(get_db)) -> TaskResponse:
    ''' It looks up the task by task_id in DB and returns the full report, raises 404 if it is missing '''

    # FLOW-1: query DB for the task
    task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()

    # FLOW-2: not found — return 404
    if not task:
        raise HTTPException(status_code=404, detail=f"task '{task_id}' not found")

    return task
# =========== FUNCTION ===========
