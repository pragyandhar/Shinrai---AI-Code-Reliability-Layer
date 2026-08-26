# WHAT DOES THIS FILE DO: Scans code line by line for hardcoded API keys, passwords, tokens and other secrets.

# ================== IMPORTS ==================
import re
# ================== IMPORTS ==================


# =========== VARIABLES : regex per secret type — checked against every non-comment line ===========
SECRET_PATTERNS = {
    "api_key": r"['\"]?[a-zA-Z_][a-zA-Z0-9_]*['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9\-_]{20,})['\"]",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "github_token": r"ghp_[a-zA-Z0-9_]{36,}",
    "private_key": r"-----BEGIN (RSA|DSA|EC|PGP|OPENSSH) PRIVATE KEY-----",
    "password": r"['\"]?password['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
    "secret": r"['\"]?secret['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
}
# =========== VARIABLES : regex per secret type — checked against every non-comment line ===========


# =========== FUNCTION ===========
# ROLE: turns the count of secrets found into a single 0-100 score
def calculate_secret_score(count: int) -> float:
    ''' even one hardcoded secret is a critical finding, two or more zeroes the score out completely '''

    if count == 0:
        return 100

    if count == 1:
        return 30

    return 0
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: scans every line of the code against all secret patterns and returns score + what it found
def run_secret_detector(code: str) -> dict:
    ''' skips comment lines, runs every pattern against every remaining line, collects the matches '''

    secrets_found = []

    # FLOW-1: go line by line so we can attach a line number to whatever we find
    for line_num, line in enumerate(code.split("\n"), 1):
        if line.strip().startswith("#"):
            continue

        # FLOW-2: a single line can trip more than one pattern, we record all of them
        for secret_type, pattern in SECRET_PATTERNS.items():
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                secrets_found.append({
                    "type": secret_type,
                    "line": line_num,
                    "detail": f"Hardcoded {secret_type} detected",
                    "masked_value": line[:20] + "...",     # USE: only show a preview, never the full secret value
                })

    score = calculate_secret_score(len(secrets_found))

    return {
        "score": score,
        "tier": "CRITICAL",
        "issues": secrets_found,
        "summary": {"total_secrets": len(secrets_found)},
    }
# =========== FUNCTION ===========
