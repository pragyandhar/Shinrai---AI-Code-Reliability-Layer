# WHAT DOES THIS FILE DO: Full Shinrai pipeline — generates code, runs reliability + security, aggregates confidence, auto-repairs, documents, and saves everything to DB.

# ================== IMPORTS ==================
import traceback

from celery_worker import celery_app
from app.config import settings
from app.db.operations import TaskOperations
from app.core.llm.generator import generate_code
from app.core.reliability.runner import run_reliability_checks
from app.core.security.runner import run_security
from app.core.confidence.aggregator import aggregate_report
from app.core.repair.repairer import repair_code
from app.core.repair.retry_handler import should_retry
from app.core.utils.diff_generator import generate_diff
from app.core.utils.doc_generator import generate_documentation
from app.core.utils.logger import pipeline_logger
from app.core.utils.errors import (
    CodeGenerationError,
    ReliabilityCheckError,
    SecurityCheckError,
    DatabaseError,
)
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: full pipeline — generates code, checks it, repairs low-confidence code, documents it, saves everything to DB
@celery_app.task(bind=True, name="tasks.run_pipeline", max_retries=1)
def run_pipeline(self, task_id: str, prompt: str) -> dict:
    ''' orchestrates every Shinrai stage for one task, logging each step and mapping failures to the right custom exception '''

    try:
        # ========== STEP 1: generate code ==========
        pipeline_logger.log_event("step_1_start", task_id, {"step": "code_generation"})

        try:
            generated_code = generate_code(prompt)
        except Exception as e:
            raise CodeGenerationError(f"Failed to generate code: {str(e)}")

        TaskOperations.update_task(task_id, original_code=generated_code, status="analyzing")
        pipeline_logger.log_event("step_1_complete", task_id, {"code_length": len(generated_code)})

        # ========== STEP 2: reliability checks ==========
        pipeline_logger.log_event("step_2_start", task_id, {"step": "reliability_checks"})

        try:
            reliability_report = run_reliability_checks(generated_code)
        except Exception as e:
            raise ReliabilityCheckError(f"Reliability check failed: {str(e)}")

        pipeline_logger.log_event("step_2_complete", task_id, {"reliability_score": reliability_report.get("score", 0)})

        # ========== STEP 3: security checks ==========
        pipeline_logger.log_event("step_3_start", task_id, {"step": "security_checks"})

        try:
            security_report = run_security(generated_code)
        except Exception as e:
            raise SecurityCheckError(f"Security check failed: {str(e)}")

        pipeline_logger.log_event("step_3_complete", task_id, {"security_score": security_report.get("score", 0)})

        # ========== STEP 4: confidence aggregation + repair loop ==========
        pipeline_logger.log_event("step_4_start", task_id, {"step": "confidence_aggregation"})

        current_code = generated_code
        repair_attempts = 0

        # FLOW-1: keeps repairing while attempts remain — each pass re-aggregates confidence first so we always act on the latest code
        while repair_attempts < settings.max_repair_attempts:
            confidence_report = aggregate_report(reliability_report, security_report)
            confidence_score = confidence_report.get("confidence_score", 0)

            pipeline_logger.log_event(
                "confidence_calculated",
                task_id,
                {
                    "attempt": repair_attempts,
                    "score": confidence_score,
                    "needs_repair": confidence_report.get("needs_repair", False),
                },
            )

            if not confidence_report.get("needs_repair", False):
                pipeline_logger.log_event("repair_not_needed", task_id, {"score": confidence_score})
                break

            repair_attempts += 1

            # FLOW-2: should_retry double-checks the attempt count against settings.max_repair_attempts — this is what actually stops the loop once attempts run out
            if not should_retry(confidence_score, repair_attempts, settings.max_repair_attempts):
                pipeline_logger.log_event(
                    "repair_stopped",
                    task_id,
                    {"reason": "max_attempts_reached", "attempts": repair_attempts},
                )
                break

            pipeline_logger.log_event(
                "repair_start",
                task_id,
                {"attempt": repair_attempts, "issues_count": len(confidence_report.get("issues", []))},
            )

            try:
                current_code = repair_code(current_code, confidence_report.get("issues", []))
            except Exception as e:
                # USE: a broken repair call shouldn't fail the whole task, it just means we stop trying
                pipeline_logger.log_error("repair_failed", task_id, str(e))
                break

            try:
                reliability_report = run_reliability_checks(current_code)
                security_report = run_security(current_code)
            except Exception as e:
                pipeline_logger.log_error("recheck_failed", task_id, str(e))
                break

            pipeline_logger.log_event(
                "repair_complete",
                task_id,
                {
                    "attempt": repair_attempts,
                    "new_reliability": reliability_report.get("score", 0),
                    "new_security": security_report.get("score", 0),
                },
            )

        # FLOW-3: whatever the loop landed on — repaired or not — this is the score that decides everything downstream
        confidence_report = aggregate_report(reliability_report, security_report)

        pipeline_logger.log_event(
            "step_4_complete",
            task_id,
            {"repair_attempts": repair_attempts, "final_score": confidence_report.get("confidence_score", 0)},
        )

        # ========== STEP 5: diff + documentation ==========
        pipeline_logger.log_event("step_5_start", task_id, {"step": "diff_and_documentation"})

        diff_text = generate_diff(generated_code, current_code)
        documentation = generate_documentation(current_code, reliability_report, security_report)

        pipeline_logger.log_event("step_5_complete", task_id, {"diff_length": len(diff_text)})

        # ========== STEP 6: output state ==========
        confidence_score = confidence_report.get("confidence_score", 0)

        if confidence_score >= 85:
            output_state = "Production Ready"
        elif confidence_score >= 40:
            output_state = "Review Recommended"
        else:
            output_state = "Manual Review Required"

        pipeline_logger.log_event("output_state_determined", task_id, {"output_state": output_state, "score": confidence_score})

        # ========== STEP 7: save to database ==========
        pipeline_logger.log_event("step_7_start", task_id, {"step": "save_to_database"})

        try:
            success = TaskOperations.save_reports(
                task_id,
                reliability=reliability_report,
                security=security_report,
                confidence=confidence_report,
                fixed_code=current_code if current_code != generated_code else None,
                diff=diff_text if diff_text else None,
                documentation=documentation,
                repair_attempts=repair_attempts,
                output_state=output_state,
            )

            if not success:
                raise DatabaseError(f"Failed to save reports for {task_id}")
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(str(e))

        pipeline_logger.log_event("step_7_complete", task_id, {"status": "completed"})
        pipeline_logger.log_event(
            "pipeline_success",
            task_id,
            {"output_state": output_state, "repair_attempts": repair_attempts},
        )

        return {"task_id": task_id, "status": "completed", "output_state": output_state}

    except Exception as e:
        pipeline_logger.log_error("pipeline_failed", task_id, str(e), trace=traceback.format_exc())

        # USE: best-effort status update — if this also fails, we still want the retry below to fire
        try:
            TaskOperations.update_task(task_id, status="failed", output_state="Error")
        except Exception:
            pass

        raise self.retry(exc=e, countdown=5, max_retries=1)
# =========== FUNCTION ===========
