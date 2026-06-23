# WHAT DOES THIS FILE DO: Runs mypy static type checker on a code string and returns a score + list of errors.

# ================== IMPORTS ==================
import os
import re
import subprocess
import tempfile
# ================== IMPORTS ==================


# =========== VARIABLES : regex to parse one mypy output line ===========
MYPY_LINE_PATTERN = re.compile(
    r"^.+:(?P<line>\d+): (?P<severity>\w+): (?P<message>.+?)(?:\s+\[(?P<code>[^\]]+)\])?$"
)
# =========== VARIABLES : regex to parse one mypy output line ===========


# =========== FUNCTION ===========
# ROLE: It runs mypy on the given code and returns type error score and issues as JSON
def check_types(code: str) -> dict:
    ''' It writes code to temporary file, runs mypy on it, parses text output, returns score and issues then clears the temporary file '''

    tmp_path = None

    try:
        # FLOW-1: write code to temp file — mypy does not support stdin
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        # FLOW-2: run mypy with clean output flags
        result = subprocess.run(
            [
                "mypy",
                "--ignore-missing-imports",   # USE: If generated code will have imports we cannot resolve locally
                "--no-error-summary",         # USE: It skips the "Found X errors" footer because we don't need it
                "--no-pretty",                # USE: No colours or decorations, it gives only plain output
                tmp_path,
            ],
            capture_output=True,
            text=True,
        )

        # FLOW-3: parse each output line — only keep "error" severity, skip notes and warnings
        issues = []
        for line in result.stdout.splitlines():
            match = MYPY_LINE_PATTERN.match(line)
            if not match:
                continue

            if match.group("severity") != "error":
                continue

            issues.append({
                "line": int(match.group("line")),
                "severity": match.group("severity"),
                "code": match.group("code"),
                "message": match.group("message"),
            })

        # FLOW-4: calculate score — start at 100, deduct 5 per error, floor at 0
        score = max(0, 100 - (len(issues) * 5))

        return {
            "score": score,
            "tier": "HIGH",
            "issues": issues,
        }

    finally:
        # cleanup temp file no matter what happens
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)     # USE: mypy can't use stdin so we must clean up manually
# =========== FUNCTION ===========
