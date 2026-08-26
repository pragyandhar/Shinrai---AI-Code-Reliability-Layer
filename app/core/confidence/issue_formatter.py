# WHAT DOES THIS FILE DO: Turns reliability + security breakdowns into one flat list of actionable issues.


# =========== VARIABLES : tier -> severity label shown to the user ===========
SEVERITY_BY_TIER = {
    "critical": "CRITICAL",
    "major": "HIGH",
    "minor": "MEDIUM",
}
# =========== VARIABLES : tier -> severity label shown to the user ===========


# =========== VARIABLES : check name -> generic fix suggestion, covers checks that exist today and the security checks phase-4 will add ===========
SUGGESTIONS = {
    "linter": "Clean up the flagged style/lint violation.",
    "type_checker": "Fix the type mismatch reported by mypy.",
    "hallucination": "Remove or replace the unresolved import — it does not exist in this environment.",
    "sandbox": "Fix the runtime error before this code can run safely.",
    "flow_analyzer": "Fix the logic flow issue described above.",
    "sast": "Fix the flagged security vulnerability pattern.",
    "cve_check": "Upgrade the vulnerable dependency to a patched version.",
    "secret_detection": "Remove the hardcoded secret and use environment variables instead.",
    "dangerous_patterns": "Replace the dangerous call with a safer alternative.",
}
DEFAULT_SUGGESTION = "Review and fix this issue before shipping."
# =========== VARIABLES : check name -> generic fix suggestion, covers checks that exist today and the security checks phase-4 will add ===========


# =========== FUNCTION ===========
# ROLE: turns one check's raw issue list into the standard actionable-issue shape
def _extract_issues_for_check(layer: str, check: str, tier: str, raw_issues: list) -> list:
    ''' every check returns issues in its own shape, this pulls line + detail out of whatever it gets '''

    formatted = []

    # FLOW-1: each raw issue has a different set of keys depending on which check produced it, so we take whatever is there
    for issue in raw_issues:
        line = issue.get("line")     # USE: hallucination and sandbox issues don't have a line at all, that's fine

        # FLOW-2: most checks put their message in "message" or "detail" — pattern_scanner is the odd one out, it only has "pattern" (e.g. "os.system")
        if issue.get("message"):
            detail = issue["message"]
        elif issue.get("detail"):
            detail = issue["detail"]
        elif issue.get("pattern"):
            detail = f"dangerous pattern detected: {issue['pattern']}"
        else:
            detail = str(issue)

        # FLOW-3: pattern_scanner already carries its own specific fix per pattern — that beats the generic per-check suggestion
        suggestion = issue.get("suggestion") or SUGGESTIONS.get(check, DEFAULT_SUGGESTION)

        formatted.append({
            "layer": layer,
            "check": check,
            "severity": SEVERITY_BY_TIER.get(tier, "MEDIUM"),
            "line": line,
            "detail": detail,
            "suggestion": suggestion,
        })

    return formatted
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: walks one layer's report (reliability or security) and collects issues from checks whose tier + score cross the threshold
def _format_layer(layer: str, report: dict, tiers_to_flag: set) -> list:
    ''' only checks in tiers_to_flag with score below 50 get reported, then their issues are pulled from wherever this layer keeps them '''

    breakdown = report.get("breakdown", {})
    details = report.get("details", {})
    collected = []

    # FLOW-1: go check by check in the breakdown — that's where tier + score live. tier casing differs between layers (reliability uses lowercase, security uses uppercase) so we normalize before comparing
    for check, meta in breakdown.items():
        tier = meta["tier"].lower()

        if tier not in tiers_to_flag:
            continue

        if meta["score"] >= 50:
            continue

        # FLOW-2: score is bad enough and tier matters — reliability keeps issues in a separate "details" dict, security embeds them right in the breakdown entry, so we check both
        check_issues = details.get(check, {}).get("issues") or meta.get("issues", [])
        collected += _extract_issues_for_check(layer, check, tier, check_issues)

    return collected
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: combines reliability + security into one actionable issue list for the confidence report
def format_issues(reliability: dict, security: dict) -> list:
    ''' reliability flags critical and major tier failures, security only flags critical tier failures '''

    # FLOW-1: reliability — critical or major tier, low score, gets reported
    issues = _format_layer("reliability", reliability, tiers_to_flag={"critical", "major"})

    # FLOW-2: security — only critical tier, low score, gets reported (secret leaks, sandbox escapes)
    issues += _format_layer("security", security, tiers_to_flag={"critical"})

    return issues
# =========== FUNCTION ===========
