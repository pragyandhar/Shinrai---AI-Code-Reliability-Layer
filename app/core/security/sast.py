# WHAT DOES THIS FILE DO: Runs Bandit static security analysis on a code string and returns a score + issues.

# ================== IMPORTS ==================
import json
import subprocess
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: turns bandit's high/medium/low counts into a single 0-100 score
def calculate_sast_score(high: int, medium: int, low: int) -> float:
    ''' one HIGH severity finding is enough to tank the score, LOW findings barely move it '''

    # FLOW-1: worst finding present decides the score — HIGH beats MEDIUM beats LOW
    if high > 0:
        return 20

    if medium > 0:
        return 55

    if low > 0:
        return 80

    return 100
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: runs bandit on the given code via stdin and returns score + issues
def run_sast(code: str) -> dict:
    ''' pipes code into bandit, parses its JSON output, counts findings by severity, scores them '''

    try:
        # FLOW-1: bandit reads from stdin with "-", -f json gives us parseable output
        result = subprocess.run(
            ["bandit", "-f", "json", "-"],
            input=code,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # FLOW-2: bandit's json output has a "results" list, one entry per finding
        output = json.loads(result.stdout)
        results = output.get("results", [])

        high_count = len([r for r in results if r["severity"] == "HIGH"])
        medium_count = len([r for r in results if r["severity"] == "MEDIUM"])
        low_count = len([r for r in results if r["severity"] == "LOW"])

        score = calculate_sast_score(high_count, medium_count, low_count)

        # FLOW-3: build our own issue shape from bandit's raw finding fields
        issues = [
            {
                "type": "SAST Vulnerability",
                "line": r.get("line_number"),
                "severity": r["severity"],
                "detail": r.get("issue_text"),
                "test_id": r.get("test_id"),
            }
            for r in results
        ]

        return {
            "score": score,
            "tier": "MAJOR",
            "issues": issues,
            "summary": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count,
            },
        }

    except subprocess.TimeoutExpired:
        return {"score": 20, "tier": "MAJOR", "issues": [], "error": "SAST timeout"}

    except Exception as e:
        # USE: covers bandit not being installed (FileNotFoundError) and any bad/unparseable output
        return {"score": 20, "tier": "MAJOR", "issues": [], "error": str(e)}
# =========== FUNCTION ===========
