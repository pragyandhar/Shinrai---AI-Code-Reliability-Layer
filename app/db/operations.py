# WHAT DOES THIS FILE DO: Single source of truth for all task CRUD operations — pipeline and routes both go through this instead of touching SQLAlchemy directly.

# ================== IMPORTS ==================
import uuid
from datetime import datetime

from app.models.db import AnalysisTask, SessionLocal
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: groups every DB operation a task record needs, each method opens and closes its own session
class TaskOperations:
    ''' every method here is a staticmethod — this class is just a namespace, it holds no state of its own '''

    # FLOW-1: creates a new queued task row and hands back its id so the caller can start polling on it
    @staticmethod
    def create_task(prompt: str) -> str:
        ''' inserts a fresh row with status "queued", returns the generated task_id '''

        db = SessionLocal()
        task_id = str(uuid.uuid4())

        try:
            task = AnalysisTask(
                task_id=task_id,
                status="queued",
                prompt=prompt,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(task)
            db.commit()

            return task_id
        finally:
            db.close()

    # FLOW-2: plain lookup by id, used by the report endpoint and anywhere else that needs the current row
    @staticmethod
    def get_task(task_id: str) -> AnalysisTask | None:
        ''' returns the task row, or None if no task with that id exists '''

        db = SessionLocal()

        try:
            task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()

            return task
        finally:
            db.close()

    # FLOW-3: generic field updater — pipeline calls this at every step instead of writing its own query-mutate-commit each time
    @staticmethod
    def update_task(task_id: str, **kwargs) -> bool:
        ''' sets whatever fields are passed in kwargs on the task row, returns False if the task doesn't exist '''

        db = SessionLocal()

        try:
            task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()

            if not task:
                return False

            # FLOW-4: only set attributes the model actually has — silently ignores anything else passed by mistake
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            task.updated_at = datetime.utcnow()
            db.commit()

            return True
        finally:
            db.close()

    # FLOW-5: the one big write at the end of the pipeline — bundles every report + the fixed code into a single update_task call
    @staticmethod
    def save_reports(
        task_id: str,
        reliability: dict,
        security: dict,
        confidence: dict,
        fixed_code: str = None,
        diff: str = None,
        documentation: str = None,
        repair_attempts: int = 0,
        output_state: str = None,
    ) -> bool:
        ''' marks the task completed and writes every report + repair result it produced '''

        return TaskOperations.update_task(
            task_id,
            reliability_report=reliability,
            security_report=security,
            confidence_report=confidence,
            fixed_code=fixed_code,
            diff=diff,
            documentation=documentation,
            repair_attempt=repair_attempts,     # USE: DB column is singular "repair_attempt", kwarg here stays plural to match the spec's calling convention
            output_state=output_state,
            status="completed",
        )
# =========== FUNCTION ===========
