# Phase 5 — Confidence Aggregator & Auto-Repair Loop
> Combine scores + trigger repairs for low-confidence code

---

## Table of Contents
1. [Overview](#1-overview)
2. [Files to Build](#2-files-to-build)
3. [Pipeline Flow](#3-pipeline-flow)
4. [File Breakdown](#4-file-breakdown)
5. [Integration Points](#5-integration-points)
6. [Error Handling](#6-error-handling)

---

## 1. Overview

Reliability Score + Security Score → Weakest Link algorithm → Confidence Score + Risk Label + Actionable Issues

If score < 40 anywhere → trigger auto-repair → re-run full checks → final output

---

## 2. Files to Build

```
app/core/confidence/
├── aggregator.py        # Main orchestrator
├── risk_labels.py       # Score → label mapping
└── issue_formatter.py   # Format issues for user

app/core/repair/
├── repairer.py          # GPT-4o repair prompt logic
└── retry_handler.py     # Retry counter + state management
```

**Update:**
- `app/tasks/pipeline.py` — add repair loop logic

---

## 3. Pipeline Flow

```
Reliability Report (score + breakdown)
Security Report (score + breakdown)
        │
        ▼
[Confidence Aggregator]
        │
        ├─→ Weakest Link Algorithm
        │   └─→ final_confidence_score
        │
        ├─→ Risk Label Assignment
        │   └─→ "Production Ready" / "Needs Review" / etc
        │
        └─→ Issue Formatter
            └─→ actionable_issues list
                    │
                    ▼
            Score check: is any < 40?
            ┌─────────────────────┐
            │  YES                │  NO
            ▼                     ▼
        [Repair Loop]         [Save to DB]
        (Max 3 retries)       status: completed
            │
            ├─→ Retry counter < 3?
            │   ├─ YES → GPT-4o re-prompt with issues
            │   └─ NO → manual_review_required
            │
            ├─→ Repaired code
            │
            ├─→ Re-run Reliability + Security
            │
            ├─→ Confidence Aggregator again
            │
            └─→ Check score again
                    │
                    └─→ Still < 40? → retry again
                        Else → Save fixed code
```

---

## 4. File Breakdown

### File 1 — `app/core/confidence/risk_labels.py`

**Kaam:** Score → Risk Label mapping

```python
# Stateless mapping function

def get_risk_label(score: float) -> dict:
    """
    score (0-100) → label + color + status
    """
    
    if score >= 85:
        return {
            "label": "Production Ready",
            "color": "green",
            "emoji": "🟢",
            "deploy": True
        }
    elif score >= 65:
        return {
            "label": "Needs Minor Fixes",
            "color": "yellow",
            "emoji": "🟡",
            "deploy": False
        }
    elif score >= 40:
        return {
            "label": "Significant Issues",
            "color": "orange",
            "emoji": "🟠",
            "deploy": False
        }
    else:
        return {
            "label": "Not Safe to Deploy",
            "color": "red",
            "emoji": "🔴",
            "deploy": False
        }
```

---

### File 2 — `app/core/confidence/issue_formatter.py`

**Kaam:** Reliability + Security breakdown → actionable issues list

Input:
```python
reliability = {
    "score": 78,
    "breakdown": {
        "sandbox": {"score": 60, "tier": "CRITICAL", "errors": [...]}
    }
}

security = {
    "score": 65,
    "breakdown": {
        "pattern_scanner": {"score": 30, "tier": "CRITICAL", "issues": [...]}
    }
}
```

Output:
```python
[
    {
        "layer": "reliability",
        "check": "sandbox_execution",
        "severity": "HIGH",
        "line": 42,
        "detail": "RuntimeError: division by zero",
        "suggestion": "Add input validation before division"
    },
    {
        "layer": "security",
        "check": "pattern_scanner",
        "severity": "CRITICAL",
        "line": 18,
        "detail": "os.system() detected",
        "suggestion": "Use subprocess.run with shell=False"
    }
]
```

Logic:
```
Iterate reliability breakdown:
    → Tier CRITICAL or MAJOR + score < 50 → add to issues
    → Extract error details + line numbers from errors/issues
    → Generate suggestion based on error type

Iterate security breakdown:
    → Tier CRITICAL + score < 50 → add to issues
    → Extract flagged patterns/secrets
    → Generate suggestion
```

---

### File 3 — `app/core/confidence/aggregator.py`

**Kaam:** Main orchestrator — calculate final confidence using Weakest Link

```python
def calculate_confidence(
    reliability_score: float,
    security_score: float
) -> float:
    """
    Weakest Link algorithm
    """
    
    base = (reliability_score * 0.5) + (security_score * 0.5)
    min_score = min(reliability_score, security_score)
    
    # Critical penalty
    if min_score < 40:
        penalty = (40 - min_score) * 0.5
        base -= penalty
    
    return round(max(0, base), 2)


def aggregate_report(reliability: dict, security: dict) -> dict:
    """
    Combine both reports → full confidence report
    """
    
    confidence_score = calculate_confidence(
        reliability["score"],
        security["score"]
    )
    
    risk_label = get_risk_label(confidence_score)
    actionable_issues = format_issues(reliability, security)
    
    return {
        "confidence_score": confidence_score,
        "risk_label": risk_label["label"],
        "emoji": risk_label["emoji"],
        "deploy_safe": risk_label["deploy"],
        "issues": actionable_issues,
        "needs_repair": confidence_score < 40
    }
```

---

### File 4 — `app/core/repair/repairer.py`

**Kaam:** Low-confidence code को GPT-4o से फिर से ठीक करो

```python
from app.core.llm.generator import generate_code

def create_repair_prompt(
    original_code: str,
    actionable_issues: list
) -> str:
    """
    Structured prompt to GPT-4o for repair
    """
    
    issues_text = "\n".join([
        f"- [{issue['severity']}] Line {issue['line']}: {issue['detail']}"
        for issue in actionable_issues
    ])
    
    prompt = f"""
    You are a Python code repair expert. Fix the following code based on these issues:
    
    ISSUES TO FIX:
    {issues_text}
    
    ORIGINAL CODE:
    ```python
    {original_code}
    ```
    
    REQUIREMENTS:
    1. Fix all listed issues
    2. Keep the same functionality
    3. Return ONLY the repaired code, no explanations
    4. Ensure code is production-ready
    
    REPAIRED CODE:
    """
    
    return prompt


def repair_code(
    original_code: str,
    actionable_issues: list
) -> str:
    """
    Call GPT-4o to repair code
    """
    
    prompt = create_repair_prompt(original_code, actionable_issues)
    repaired = generate_code(prompt)  # Reuse generator from Phase 2
    
    return repaired
```

---

### File 5 — `app/core/repair/retry_handler.py`

**Kaam:** Repair attempts track karo — max 3

```python
def should_retry(
    confidence_score: float,
    repair_attempts: int,
    max_attempts: int = 3
) -> bool:
    """
    Decide if we should retry repair
    """
    
    if repair_attempts >= max_attempts:
        return False  # Max attempts reached
    
    if confidence_score >= 40:
        return False  # Score acceptable
    
    return True  # Retry


def get_retry_message(repair_attempts: int, max_attempts: int) -> str:
    """
    Message for user based on retry count
    """
    
    if repair_attempts == 0:
        return "Initial analysis complete. Quality score < 40. Auto-repairing..."
    elif repair_attempts < max_attempts:
        return f"Repair attempt {repair_attempts}/{max_attempts}..."
    else:
        return f"Max repair attempts ({max_attempts}) reached. Manual review recommended."
```

---

## 5. Integration Points

### Update `app/tasks/pipeline.py`

```python
from celery import group, chord
from app.core.reliability.runner import run_reliability
from app.core.security.runner import run_security
from app.core.confidence.aggregator import aggregate_report
from app.core.repair.repairer import repair_code
from app.core.repair.retry_handler import should_retry

@celery_app.task
def run_pipeline(task_id: str, prompt: str):
    """
    Main pipeline with auto-repair loop
    """
    
    # Step 1: Generate code
    generated_code = generate_code(prompt)
    db_update(task_id, {"generated_code": generated_code, "status": "checking"})
    
    # Step 2: Run Reliability + Security in parallel (Celery chord)
    rel_result = run_reliability(generated_code)
    sec_result = run_security(generated_code)
    
    # Step 3: Aggregate confidence
    current_code = generated_code
    repair_attempts = 0
    
    while repair_attempts < 3:
        conf_report = aggregate_report(rel_result, sec_result)
        
        if not conf_report["needs_repair"]:
            # ✅ Score acceptable
            break
        
        # ❌ Score < 40, try repair
        repair_attempts += 1
        current_code = repair_code(current_code, conf_report["issues"])
        
        # Re-check repaired code
        rel_result = run_reliability(current_code)
        sec_result = run_security(current_code)
    
    # Step 4: Final output state
    final_conf = aggregate_report(rel_result, sec_result)
    
    if final_conf["confidence_score"] >= 85:
        output_state = "Production Ready"
    elif final_conf["confidence_score"] >= 40:
        output_state = "Review Recommended"
    else:
        output_state = "Manual Review Required"
    
    # Step 5: Save to DB
    db_update(task_id, {
        "original_code": generated_code,
        "fixed_code": current_code if current_code != generated_code else None,
        "reliability_report": rel_result,
        "security_report": sec_result,
        "confidence_report": final_conf,
        "repair_attempts": repair_attempts,
        "output_state": output_state,
        "status": "completed"
    })
```

---

## 6. Error Handling

### Repair Prompt Failure
```python
try:
    repaired = repair_code(current_code, issues)
except Exception as e:
    # If repair fails, keep current code and mark as needs_manual_review
    output_state = "Manual Review Required"
    logger.error(f"Repair failed for {task_id}: {str(e)}")
```

### Network Timeout
```python
from requests.exceptions import Timeout

try:
    repaired = repair_code(current_code, issues)
except Timeout:
    # Timeout → manual review
    output_state = "Manual Review Required"
    logger.warning(f"Repair timeout for {task_id}")
```

### Infinite Loop Prevention
```python
# Already handled by max_repair_attempts = 3
# If score < 40 after 3 retries → output_state = "Manual Review Required"
```

---

## Summary

**4 new files + 1 update:**

```
risk_labels.py       ← Score → label mapping
issue_formatter.py   ← Breakdown → actionable issues
aggregator.py        ← Weakest Link algorithm
repairer.py          ← GPT-4o repair prompt
retry_handler.py     ← Retry logic
pipeline.py          ← UPDATED — add repair loop
```

---

## Git Commit Message

```
feat(phase-5): confidence aggregator with auto-repair loop and weakest link scoring

- Implement Weakest Link algorithm for final confidence score calculation
- Add risk label assignment (Production Ready / Needs Review / Not Safe)
- Create actionable issue formatter combining reliability + security breakdowns
- Integrate auto-repair loop with max 3 retries using Azure Foundry re-prompting
- Add retry handler with score-based decision logic and manual review fallback
- Update pipeline task to orchestrate full flow with repair attempts
```

---

*Shinrai — Phase 5 ready for implementation*