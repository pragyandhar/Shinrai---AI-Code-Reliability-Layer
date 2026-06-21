# WHAT DOES THIS FILE DO: Main Celery pipeline task — generates code and runs all analysis steps in sequence.

# ================== IMPORTS ==================
from celery_worker import celery_app
from app.core.llm.generator import generate_code
from app.models.db import SessionLocal, AnalysisTask
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: full pipeline - generates code, run checks, save results to DB
@celery_app.task(name="tasks.run_pipeline")
def run_pipeline(task_id: str, prompt: str) -> None:
    ''' It orchestrates the full shinrai pipeline for a given task_id and prompt '''

    db = SessionLocal()

    try:
        # FLOW-1: generate code from the prompt
        generated_code = generate_code(prompt)

        # FLOW-2: reliability check — placeholder till Phase 3
        reliability_result = None

        # FLOW-3: security check — placeholder till Phase 3
        security_result = None

        # FLOW-4: confidence score — placeholder till Phase 4
        confidence_result = None

        # FLOW-5: fetch the task record and save results to DB
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        task.original_code = generated_code
        task.reliability_report = reliability_result
        task.security_report = security_result
        task.confidence_report = confidence_result
        task.status = "completed"

        db.commit()

    except Exception as e:
        # something broke — mark task as failed so it doesn't hang
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if task:
            task.status = "failed"
            db.commit()

        raise e

    finally:
        db.close()
# =========== FUNCTION ===========
