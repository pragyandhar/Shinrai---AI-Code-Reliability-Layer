# WHAT DOES THIS FILE DO: Orchestrates all reliability checks on a code string and returns the full reliability report.

# ================== IMPORTS ==================
from app.core.reliability.linter import lint_code
from app.core.reliability.type_checker import check_types
from app.core.reliability.hallucination import check_hallucinations
from app.core.reliability.sandbox import run_sandbox
from app.core.reliability.flow_analyzer import analyze_flow
from app.core.reliability.scorer import calculate_reliability_score
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: runs all five reliability checks on the given code and returns the combined reliability report
def run_reliability_checks(code: str) -> dict:
    ''' calls each check, feeds scores to the scorer, returns final score + label + full per-check details '''

    # FLOW-1: run all five checks — each returns its own result dict with score, tier, issues
    linter_result   = lint_code(code)
    type_result     = check_types(code)
    halluc_result   = check_hallucinations(code)
    sandbox_result  = run_sandbox(code)
    flow_result     = analyze_flow(code)

    # FLOW-2: pull just the scores out — scorer only needs the numeric scores keyed by check name
    scores = {
        "linter":        linter_result["score"],
        "type_checker":  type_result["score"],
        "hallucination": halluc_result["score"],
        "sandbox":       sandbox_result["score"],
        "flow_analyzer": flow_result["score"],
    }

    # FLOW-3: feed scores into scorer — it applies weights, ceiling, and penalty to get final score
    scored = calculate_reliability_score(scores)

    # FLOW-4: combine final score with full per-check details and return as one report
    return {
        "score":     scored["score"],
        "label":     scored["label"],
        "breakdown": scored["breakdown"],
        "details": {
            "linter":        linter_result,
            "type_checker":  type_result,
            "hallucination": halluc_result,
            "sandbox":       sandbox_result,
            "flow_analyzer": flow_result,
        },
    }
# =========== FUNCTION ===========
