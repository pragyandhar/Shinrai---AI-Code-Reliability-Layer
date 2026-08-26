# WHAT DOES THIS FILE DO: Combines the four security check scores into one final tiered security score + breakdown.

# =========== VARIABLES : tier config for each security check — weights must sum to 1.0 ===========
SECURITY_TIER_WEIGHTS = {
    "secret_detector": {"weight": 0.30, "tier": "critical"},
    "pattern_scanner": {"weight": 0.30, "tier": "critical"},
    "sast": {"weight": 0.25, "tier": "major"},
    "cve_checker": {"weight": 0.15, "tier": "minor"},
}
# =========== VARIABLES : tier config for each security check — weights must sum to 1.0 ===========


# =========== FUNCTION ===========
# ROLE: takes the four individual check scores and produces the final weighted + penalized security score
def calculate_security_score(sast_score: float, cve_score: float, secret_score: float, pattern_score: float) -> float:
    ''' same tiered rules as the reliability scorer — critical failure caps the score, major failure penalizes it '''

    scores = {
        "secret_detector": secret_score,
        "pattern_scanner": pattern_score,
        "sast": sast_score,
        "cve_checker": cve_score,
    }

    # FLOW-1: weighted base — every check pulls the score toward its own weight
    weighted = sum(
        scores[key] * SECURITY_TIER_WEIGHTS[key]["weight"]
        for key in scores
    )

    # FLOW-2: a critical check failing (secret leak or dangerous pattern) caps the whole score, no matter how good the rest looks
    for key, meta in SECURITY_TIER_WEIGHTS.items():
        if meta["tier"] == "critical" and scores[key] < 40:
            weighted = min(weighted, 45)

    # FLOW-3: sast failing on its own doesn't cap the score, just takes a chunk off it
    for key, meta in SECURITY_TIER_WEIGHTS.items():
        if meta["tier"] == "major" and scores[key] < 40:
            weighted *= 0.80

    return round(weighted, 2)
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: formats the four raw check results into the breakdown structure the confidence layer reads from
def build_security_breakdown(sast: dict, cve: dict, secret: dict, pattern: dict) -> dict:
    ''' every check's score, tier, summary and issues get keyed by the check's public name '''

    return {
        "sast": {
            "score": sast["score"],
            "tier": sast["tier"],
            "summary": sast.get("summary", {}),
            "issues": sast.get("issues", []),
        },
        "cve_check": {
            "score": cve["score"],
            "tier": cve["tier"],
            "summary": cve.get("summary", {}),
            "issues": cve.get("issues", []),
        },
        "secret_detection": {
            "score": secret["score"],
            "tier": secret["tier"],
            "summary": secret.get("summary", {}),
            "issues": secret.get("issues", []),
        },
        "dangerous_patterns": {
            "score": pattern["score"],
            "tier": pattern["tier"],
            "summary": pattern.get("summary", {}),
            "issues": pattern.get("issues", []),
        },
    }
# =========== FUNCTION ===========
