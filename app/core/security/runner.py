# WHAT DOES THIS FILE DO: Orchestrates all four security checks on a code string and returns the full security report.

# ================== IMPORTS ==================
from app.core.security.sast import run_sast
from app.core.security.cve_checker import run_cve_check
from app.core.security.secret_detector import run_secret_detector
from app.core.security.pattern_scanner import run_pattern_scanner
from app.core.security.scorer import calculate_security_score, build_security_breakdown
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: runs all four security checks on the given code and returns the combined security report
def run_security(code: str) -> dict:
    ''' calls each check, feeds scores to the scorer, returns final score + breakdown + one flat issue list '''

    # FLOW-1: run all four checks — each is independent of the others, none needs another's result
    sast_result = run_sast(code)
    cve_result = run_cve_check(code)
    secret_result = run_secret_detector(code)
    pattern_result = run_pattern_scanner(code)

    # FLOW-2: combine the four scores into one tiered final score
    final_score = calculate_security_score(
        sast_result["score"],
        cve_result["score"],
        secret_result["score"],
        pattern_result["score"],
    )

    # FLOW-3: breakdown keeps each check's own score, tier and issues under its public name
    breakdown = build_security_breakdown(sast_result, cve_result, secret_result, pattern_result)

    # FLOW-4: flatten every check's issues into one list, tagging each with which check found it
    all_issues = (
        [{**issue, "check": "sast"} for issue in sast_result.get("issues", [])]
        + [{**issue, "check": "cve_checker"} for issue in cve_result.get("issues", [])]
        + [{**issue, "check": "secret_detection"} for issue in secret_result.get("issues", [])]
        + [{**issue, "check": "dangerous_patterns"} for issue in pattern_result.get("issues", [])]
    )

    return {
        "score": final_score,
        "breakdown": breakdown,
        "issues": all_issues,
        "total_issues": len(all_issues),
    }
# =========== FUNCTION ===========
