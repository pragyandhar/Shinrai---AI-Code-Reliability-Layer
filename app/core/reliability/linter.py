# WHAT DOES THIS FILE DO: Runs ruff linter on a code string via stdin and returns a score + list of issues found.

# ================== IMPORTS ==================
import json
import subprocess
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: lints the given code string using ruff and returns score + issues
def lint_code(code: str) -> dict:
    ''' pipes code into ruff via stdin, parses JSON output, returns score and issues '''

    # FLOW-1: run ruff — '-' tells ruff to read from stdin, --stdin-filename gives it a .py context
    result = subprocess.run(
        ["ruff", "check", "--output-format", "json", "--stdin-filename", "dummy.py", "-"],
        input=code,
        capture_output=True,
        text=True,
    )

    # FLOW-2: returncode 2 means ruff itself crashed — it is not just "issues found"
    if result.returncode == 2:
        return {
            "score": 0,
            "tier": "LOW",
            "issues": [{"line": None, "col": None, "code": "RUFF_ERROR", "message": result.stderr.strip()}],
        }

    # FLOW-3: parse JSON output — empty stdout means no issues
    raw_issues = json.loads(result.stdout) if result.stdout.strip() else []

    issues = [
        {
            "line": issue["location"]["row"],
            "col": issue["location"]["column"],
            "code": issue["code"],
            "message": issue["message"],
        }
        for issue in raw_issues
    ]

    # FLOW-4: calculate score — start at 100, deduct 5 per issue, floor at 0
    score = max(0, 100 - (len(issues) * 5))

    return {
        "score": score,
        "tier": "LOW",
        "issues": issues,
    }
# =========== FUNCTION ===========
