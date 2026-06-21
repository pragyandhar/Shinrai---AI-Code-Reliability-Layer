# WHAT DOES THIS FILE DO: POST /generate endpoint — takes a prompt, queues the full pipeline task, returns task_id.

# ================== IMPORTS ==================
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.db import get_db, AnalysisTask
from app.tasks.pipeline import run_pipeline
# ================== IMPORTS ==================


# =========== VARIABLES : Schemas — inline for now, will move to schemas/report.py later ===========
class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    task_id: str
    status: str
# =========== VARIABLES : Schemas — inline for now, will move to schemas/report.py later ===========


router = APIRouter()


# =========== FUNCTION ===========
# ROLE: receives a prompt, creates a DB task record, fires Celery pipeline, returns task_id
@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest, db: Session = Depends(get_db)) -> GenerateResponse:
    ''' queues a full pipeline run for the given prompt and returns the task_id to poll '''

    # FLOW-1: generate a unique task_id for this request
    task_id = str(uuid4())

    # FLOW-2: insert task into DB with status queued before firing the celery task
    task = AnalysisTask(
        task_id=task_id,
        prompt=request.prompt,
        status="queued",
    )
    db.add(task)
    db.commit()

    # FLOW-3: hand off to Celery — non-blocking, pipeline runs in background
    run_pipeline.delay(task_id, request.prompt)

    return GenerateResponse(task_id=task_id, status="queued")
# =========== FUNCTION ===========
