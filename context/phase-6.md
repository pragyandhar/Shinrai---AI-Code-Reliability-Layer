# Phase 6 — Complete Pipeline Integration
> End-to-end orchestration, database operations, logging, documentation generation, diff tracking

---

## Table of Contents
1. [Overview](#1-overview)
2. [Files to Build](#2-files-to-build)
3. [Complete Pipeline Flow](#3-complete-pipeline-flow)
4. [File Breakdown](#4-file-breakdown)
5. [Database Operations](#5-database-operations)
6. [Error Handling Strategy](#6-error-handling-strategy)
7. [Logging Architecture](#7-logging-architecture)
8. [Testing the Full Flow](#8-testing-the-full-flow)

---

## 1. Overview

Phase 6 ties together everything:
- LLM Generation
- Reliability Checks
- Security Checks
- Auto-Repair Loop
- Confidence Scoring
- Documentation Generation
- Diff Tracking

All coordinated via Celery task with proper database updates, error handling, and logging.

---

## 2. Files to Build

```
app/
├── core/
│   └── utils/
│       ├── diff_generator.py    # Generate code diff
│       ├── doc_generator.py     # Auto-generate documentation
│       ├── logger.py            # Structured logging
│       └── errors.py            # Custom exceptions
│
├── db/
│   └── operations.py            # Database CRUD operations
│
├── tasks/
│   └── pipeline.py              # UPDATED — complete end-to-end
│
└── middleware/
    └── error_handler.py         # Global error handling
```

---

## 3. Complete Pipeline Flow

```
POST /generate (task_id, prompt)
        │
        ▼
[Celery Task Started]
status = "queued"
        │
        ▼
[Step 1: Generate Code]
code = gpt4o(prompt)
db_update(task_id, original_code=code, status="checking")
        │
        ▼
[Step 2: Parallel Reliability + Security]
reliability = run_reliability(code)
security = run_security(code)
        │
        ▼
[Step 3: Confidence Aggregation]
confidence = aggregate_report(reliability, security)
        │
        ▼
[Step 4: Repair Loop Decision]
current_code = code
repair_attempts = 0
        │
        ├─→ while repair_attempts < 3 and confidence.score < 40:
        │       ├─ repair_attempts += 1
        │       ├─ current_code = repair(current_code, confidence.issues)
        │       ├─ reliability = run_reliability(current_code)
        │       ├─ security = run_security(current_code)
        │       └─ confidence = aggregate_report(reliability, security)
        │
        ▼
[Step 5: Generate Diff + Documentation]
diff = generate_diff(code, current_code)
documentation = generate_documentation(current_code, reliability, security)
        │
        ▼
[Step 6: Determine Output State]
if confidence.score >= 85:
    output_state = "Production Ready"
elif confidence.score >= 40:
    output_state = "Review Recommended"
else:
    output_state = "Manual Review Required"
        │
        ▼
[Step 7: Save to Database]
db_update(task_id, {
    fixed_code, diff, documentation,
    reliability_report, security_report, confidence_report,
    repair_attempts, output_state,
    status = "completed"
})
        │
        ▼
[Step 8: Client polls GET /report/{task_id}]
Returns full report with all data
```

---

## 4. File Breakdown

### File 1 — `app/core/utils/diff_generator.py`

**Kaam:** Generate human-readable diff between original and fixed code

```python
import difflib
from typing import List, Tuple

def generate_diff(original_code: str, fixed_code: str) -> str:
    """
    Generate unified diff showing changes
    Returns: diff string or empty if no changes
    """
    
    if original_code == fixed_code:
        return ""
    
    # Split into lines
    original_lines = original_code.splitlines(keepends=True)
    fixed_lines = fixed_code.splitlines(keepends=True)
    
    # Generate unified diff
    diff_lines = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile="original.py",
        tofile="fixed.py",
        lineterm=""
    )
    
    return "\n".join(diff_lines)


def get_diff_stats(diff_text: str) -> dict:
    """
    Extract statistics from diff
    """
    
    lines = diff_text.split("\n")
    added = len([l for l in lines if l.startswith("+")])
    removed = len([l for l in lines if l.startswith("-")])
    
    return {
        "lines_added": added,
        "lines_removed": removed,
        "total_changes": added + removed
    }
```

---

### File 2 — `app/core/utils/doc_generator.py`

**Kaam:** Auto-generate documentation showing which parts work/fail

```python
def generate_documentation(
    code: str,
    reliability_report: dict,
    security_report: dict
) -> str:
    """
    Generate markdown documentation with:
    - Code overview
    - Working functions
    - Failed functions
    - Security notes
    """
    
    reliability_issues = reliability_report.get("breakdown", {})
    security_issues = security_report.get("breakdown", {})
    
    doc = f"""# Code Analysis Report

## Generated Code
```python
{code}
```

## Reliability Analysis
- **Score:** {reliability_report.get('score', 0)}/100
- **Status:** {reliability_report.get('label', 'Unknown')}

### Checks Performed
"""
    
    # Add reliability breakdown
    for check_name, check_result in reliability_issues.items():
        doc += f"\n- **{check_name.replace('_', ' ').title()}:** {check_result.get('score', 0)}/100"
        if check_result.get('issues'):
            for issue in check_result['issues'][:3]:  # Top 3 issues
                doc += f"\n  - {issue.get('detail', 'Issue detected')}"
    
    doc += f"\n\n## Security Analysis\n- **Score:** {security_report.get('score', 0)}/100\n- **Status:** {security_report.get('label', 'Unknown')}\n\n### Security Checks\n"
    
    # Add security breakdown
    for check_name, check_result in security_issues.items():
        doc += f"\n- **{check_name.replace('_', ' ').title()}:** {check_result.get('score', 0)}/100"
        if check_result.get('issues'):
            for issue in check_result['issues'][:2]:  # Top 2 issues
                doc += f"\n  - {issue.get('detail', 'Issue detected')}"
    
    doc += "\n\n---\n*Generated by Shinrai — Trust the code you ship.*"
    
    return doc
```

---

### File 3 — `app/core/utils/logger.py`

**Kaam:** Structured logging for pipeline execution

```python
import logging
import json
from datetime import datetime
from typing import Any, Dict

class StructuredLogger:
    """Structured logging for Shinrai pipeline"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file logging"""
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event: str, task_id: str, data: Dict[str, Any]):
        """Log structured event"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "task_id": task_id,
            **data
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_error(self, event: str, task_id: str, error: str, trace: str = ""):
        """Log error with traceback"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "task_id": task_id,
            "error": error,
            "traceback": trace
        }
        
        self.logger.error(json.dumps(log_entry))


# Global logger instance
pipeline_logger = StructuredLogger("shinrai.pipeline")
```

---

### File 4 — `app/core/utils/errors.py`

**Kaam:** Custom exception classes

```python
class ShinaraiException(Exception):
    """Base exception for Shinrai"""
    pass


class CodeGenerationError(ShinaraiException):
    """Failed to generate code via LLM"""
    pass


class ReliabilityCheckError(ShinaraiException):
    """Reliability check failed"""
    pass


class SecurityCheckError(ShinaraiException):
    """Security check failed"""
    pass


class RepairError(ShinaraiException):
    """Code repair failed"""
    pass


class DatabaseError(ShinaraiException):
    """Database operation failed"""
    pass
```

---

### File 5 — `app/db/operations.py`

**Kaam:** Database CRUD operations — single source of truth

```python
from sqlalchemy.orm import Session
from app.models.db import AnalysisTask, SessionLocal
import uuid
from datetime import datetime

class TaskOperations:
    """Database operations for tasks"""
    
    @staticmethod
    def create_task(prompt: str) -> str:
        """
        Create new task in DB
        Returns: task_id
        """
        
        db = SessionLocal()
        task_id = str(uuid.uuid4())
        
        try:
            task = AnalysisTask(
                task_id=task_id,
                status="queued",
                prompt=prompt,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(task)
            db.commit()
            return task_id
        finally:
            db.close()
    
    @staticmethod
    def get_task(task_id: str) -> AnalysisTask:
        """Get task by ID"""
        
        db = SessionLocal()
        try:
            task = db.query(AnalysisTask).filter(
                AnalysisTask.task_id == task_id
            ).first()
            return task
        finally:
            db.close()
    
    @staticmethod
    def update_task(task_id: str, **kwargs) -> bool:
        """Update task fields"""
        
        db = SessionLocal()
        try:
            task = db.query(AnalysisTask).filter(
                AnalysisTask.task_id == task_id
            ).first()
            
            if not task:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            task.updated_at = datetime.utcnow()
            db.commit()
            return True
        finally:
            db.close()
    
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
        output_state: str = None
    ) -> bool:
        """Save all reports to DB"""
        
        return TaskOperations.update_task(
            task_id,
            reliability_report=reliability,
            security_report=security,
            confidence_report=confidence,
            fixed_code=fixed_code,
            diff=diff,
            documentation=documentation,
            repair_attempt=repair_attempts,
            output_state=output_state,
            status="completed"
        )
```

---

### File 6 — `app/tasks/pipeline.py` (COMPLETE)

**Kaam:** Full end-to-end pipeline orchestration

```python
from celery import shared_task
from app.config import settings
from app.db.operations import TaskOperations
from app.core.llm.generator import generate_code
from app.core.reliability.runner import run_reliability
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
    RepairError,
    DatabaseError
)


@shared_task(bind=True, max_retries=1)
def run_full_pipeline(self, task_id: str, prompt: str):
    """
    Complete Shinrai pipeline orchestration
    """
    
    try:
        # ========== STEP 1: Generate Code ==========
        pipeline_logger.log_event(
            "step_1_start",
            task_id,
            {"step": "code_generation"}
        )
        
        try:
            generated_code = generate_code(prompt)
        except Exception as e:
            raise CodeGenerationError(f"Failed to generate code: {str(e)}")
        
        TaskOperations.update_task(
            task_id,
            original_code=generated_code,
            status="analyzing"
        )
        
        pipeline_logger.log_event(
            "step_1_complete",
            task_id,
            {"code_length": len(generated_code)}
        )
        
        # ========== STEP 2: Run Reliability Checks ==========
        pipeline_logger.log_event(
            "step_2_start",
            task_id,
            {"step": "reliability_checks"}
        )
        
        try:
            reliability_report = run_reliability(generated_code)
        except Exception as e:
            raise ReliabilityCheckError(f"Reliability check failed: {str(e)}")
        
        pipeline_logger.log_event(
            "step_2_complete",
            task_id,
            {"reliability_score": reliability_report.get("score", 0)}
        )
        
        # ========== STEP 3: Run Security Checks ==========
        pipeline_logger.log_event(
            "step_3_start",
            task_id,
            {"step": "security_checks"}
        )
        
        try:
            security_report = run_security(generated_code)
        except Exception as e:
            raise SecurityCheckError(f"Security check failed: {str(e)}")
        
        pipeline_logger.log_event(
            "step_3_complete",
            task_id,
            {"security_score": security_report.get("score", 0)}
        )
        
        # ========== STEP 4: Confidence Aggregation + Repair Loop ==========
        pipeline_logger.log_event(
            "step_4_start",
            task_id,
            {"step": "confidence_aggregation"}
        )
        
        current_code = generated_code
        repair_attempts = 0
        
        while repair_attempts < settings.max_repair_attempts:
            # Aggregate confidence
            confidence_report = aggregate_report(reliability_report, security_report)
            confidence_score = confidence_report.get("confidence_score", 0)
            
            pipeline_logger.log_event(
                "confidence_calculated",
                task_id,
                {
                    "attempt": repair_attempts,
                    "score": confidence_score,
                    "needs_repair": confidence_report.get("needs_repair", False)
                }
            )
            
            # Check if repair needed
            if not confidence_report.get("needs_repair", False):
                pipeline_logger.log_event(
                    "repair_not_needed",
                    task_id,
                    {"score": confidence_score}
                )
                break
            
            # Try repair
            repair_attempts += 1
            
            if not should_retry(confidence_score, repair_attempts, settings.max_repair_attempts):
                pipeline_logger.log_event(
                    "repair_stopped",
                    task_id,
                    {
                        "reason": "max_attempts_reached",
                        "attempts": repair_attempts
                    }
                )
                break
            
            pipeline_logger.log_event(
                "repair_start",
                task_id,
                {
                    "attempt": repair_attempts,
                    "issues_count": len(confidence_report.get("issues", []))
                }
            )
            
            try:
                current_code = repair_code(current_code, confidence_report.get("issues", []))
            except Exception as e:
                pipeline_logger.log_error(
                    "repair_failed",
                    task_id,
                    str(e)
                )
                break
            
            # Re-run checks on repaired code
            try:
                reliability_report = run_reliability(current_code)
                security_report = run_security(current_code)
            except Exception as e:
                pipeline_logger.log_error(
                    "recheck_failed",
                    task_id,
                    str(e)
                )
                break
            
            pipeline_logger.log_event(
                "repair_complete",
                task_id,
                {
                    "attempt": repair_attempts,
                    "new_reliability": reliability_report.get("score", 0),
                    "new_security": security_report.get("score", 0)
                }
            )
        
        # Final confidence calculation
        confidence_report = aggregate_report(reliability_report, security_report)
        
        pipeline_logger.log_event(
            "step_4_complete",
            task_id,
            {
                "repair_attempts": repair_attempts,
                "final_score": confidence_report.get("confidence_score", 0)
            }
        )
        
        # ========== STEP 5: Generate Diff & Documentation ==========
        pipeline_logger.log_event(
            "step_5_start",
            task_id,
            {"step": "diff_and_documentation"}
        )
        
        diff_text = generate_diff(generated_code, current_code)
        documentation = generate_documentation(
            current_code,
            reliability_report,
            security_report
        )
        
        pipeline_logger.log_event(
            "step_5_complete",
            task_id,
            {"diff_length": len(diff_text)}
        )
        
        # ========== STEP 6: Determine Output State ==========
        confidence_score = confidence_report.get("confidence_score", 0)
        
        if confidence_score >= 85:
            output_state = "Production Ready"
        elif confidence_score >= 40:
            output_state = "Review Recommended"
        else:
            output_state = "Manual Review Required"
        
        pipeline_logger.log_event(
            "output_state_determined",
            task_id,
            {"output_state": output_state, "score": confidence_score}
        )
        
        # ========== STEP 7: Save to Database ==========
        pipeline_logger.log_event(
            "step_7_start",
            task_id,
            {"step": "save_to_database"}
        )
        
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
                output_state=output_state
            )
            
            if not success:
                raise DatabaseError(f"Failed to save reports for {task_id}")
        except Exception as e:
            raise DatabaseError(str(e))
        
        pipeline_logger.log_event(
            "step_7_complete",
            task_id,
            {"status": "completed"}
        )
        
        pipeline_logger.log_event(
            "pipeline_success",
            task_id,
            {
                "total_duration": "see timestamps",
                "output_state": output_state,
                "repair_attempts": repair_attempts
            }
        )
        
        return {
            "task_id": task_id,
            "status": "completed",
            "output_state": output_state
        }
    
    except Exception as e:
        pipeline_logger.log_error(
            "pipeline_failed",
            task_id,
            str(e),
            trace=traceback.format_exc()
        )
        
        # Update DB with error status
        try:
            TaskOperations.update_task(
                task_id,
                status="failed",
                output_state="Error"
            )
        except:
            pass
        
        # Retry once on transient errors
        raise self.retry(exc=e, countdown=5, max_retries=1)
```

---

### File 7 — `app/middleware/error_handler.py`

**Kaam:** Global error handling for FastAPI

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.utils.errors import ShinaraiException
import traceback


async def exception_handler(request: Request, exc: Exception):
    """Global exception handler for FastAPI"""
    
    if isinstance(exc, ShinaraiException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": exc.__class__.__name__,
                "message": str(exc),
                "path": str(request.url)
            }
        )
    
    # Generic error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "path": str(request.url)
        }
    )
```

Add to `main.py`:
```python
from app.middleware.error_handler import exception_handler
from app.core.utils.errors import ShinaraiException

app.add_exception_handler(ShinaraiException, exception_handler)
app.add_exception_handler(Exception, exception_handler)
```

---

## 5. Database Operations

### Key Operations

```python
# Create task
task_id = TaskOperations.create_task(prompt)

# Get task
task = TaskOperations.get_task(task_id)
# Returns AnalysisTask object or None

# Update during pipeline
TaskOperations.update_task(task_id, status="analyzing", original_code=code)

# Save final reports
TaskOperations.save_reports(
    task_id,
    reliability=rel_dict,
    security=sec_dict,
    confidence=conf_dict,
    fixed_code=fixed,
    diff=diff_str,
    documentation=docs,
    repair_attempts=2,
    output_state="Production Ready"
)
```

---

## 6. Error Handling Strategy

### Try-Catch at Each Layer

```
Level 1: Generation
  → CodeGenerationError → mark task failed, stop

Level 2: Reliability Check
  → ReliabilityCheckError → log, continue (fallback score)

Level 3: Security Check
  → SecurityCheckError → log, continue (fallback score)

Level 4: Repair
  → RepairError → log, skip this attempt, retry or mark manual review

Level 5: Database
  → DatabaseError → retry with exponential backoff, alert

Level 6: Global
  → Exception handler returns 500 with error details
```

---

## 7. Logging Architecture

### Log Events at Each Step

```
pipeline_start       → task_id, prompt length
step_1_start         → code generation starting
step_1_complete      → generated code length
step_2_start         → reliability checks starting
step_2_complete      → reliability score
step_3_start         → security checks starting
step_3_complete      → security score
step_4_start         → confidence aggregation
confidence_calculated → current score, repair needed?
repair_start         → attempt number, issues count
repair_complete      → new scores after repair
step_4_complete      → final confidence score, repair attempts
step_5_complete      → diff generated
output_state_determined → final state
step_7_complete      → saved to database
pipeline_success     → total duration, final state

pipeline_failed      → error type, traceback
```

---

## 8. Testing the Full Flow

### Manual Test

```bash
# 1. Start Celery worker
celery -A celery_worker worker --loglevel=info

# 2. Call API
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a FastAPI hello world endpoint"}'

# Response: {"task_id": "abc-123", "status": "queued"}

# 3. Poll for results
curl http://localhost:8000/api/v1/report/abc-123

# Keep polling until status = "completed"
```

### Expected Output

```json
{
  "task_id": "abc-123",
  "status": "completed",
  "original_code": "...",
  "reliability": {
    "score": 82,
    "label": "Needs Minor Fixes",
    "breakdown": {...}
  },
  "security": {
    "score": 88,
    "label": "Production Ready",
    "breakdown": {...}
  },
  "confidence": {
    "score": 85,
    "label": "Production Ready"
  },
  "fixed_code": "...",
  "diff": "...",
  "documentation": "...",
  "repair_attempts": 1,
  "output_state": "Production Ready"
}
```

---

## Summary

**7 new files + 1 update:**

```
diff_generator.py      ← Generate code diff
doc_generator.py       ← Auto-generate documentation
logger.py              ← Structured logging
errors.py              ← Custom exceptions
operations.py          ← Database CRUD
pipeline.py            ← COMPLETE end-to-end orchestration
error_handler.py       ← Global error handling
main.py                ← UPDATED add exception handlers
```

---

## Git Commit Message

```
feat(phase-6): complete pipeline integration with end-to-end orchestration

- Implement complete Celery task orchestrating all 7 pipeline steps
- Add diff generation using difflib for original vs fixed code comparison
- Create auto-documentation generator showing reliability and security analysis
- Build structured logging with event tracking across entire pipeline
- Add database operations layer with CRUD methods for task management
- Implement comprehensive error handling with custom exception classes
- Add global FastAPI error handler with proper status codes and messages
- Integrate repair loop with retry logic and score-based decision making
- Save complete reports (reliability, security, confidence, diff, docs) to DB
```

---

*Shinrai — Phase 6 complete integration ready*