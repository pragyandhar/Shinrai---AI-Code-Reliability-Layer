# WHAT DOES THIS FILE DO: Combines all reliability check scores into one final tiered reliability score.

# =========== VARIABLES : tier config for each reliability check — weights must sum to 1.0 ===========
RELIABILITY_TIERS = {
    "hallucination": {"weight": 0.25, "tier": "critical"},
    "sandbox":       {"weight": 0.30, "tier": "critical"},
    "type_checker":  {"weight": 0.20, "tier": "major"},
    "flow_analyzer": {"weight": 0.15, "tier": "major"},
    "linter":        {"weight": 0.10, "tier": "minor"},
}
# =========== VARIABLES : tier config for each reliability check — weights must sum to 1.0 ===========


# =========== FUNCTION ===========
# ROLE: maps a numeric score to a human-readable risk label
def get_risk_label(score: float) -> str:
    ''' returns the risk label string for a given score based on architecture-defined thresholds '''

    # FLOW-1: check score range top-down and return the matching label
    if score >= 85:
        return "Production Ready"

    if score >= 65:
        return "Needs Minor Fixes"

    if score >= 40:
        return "Significant Issues"

    return "Not Safe to Deploy"
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: takes individual check scores and produces a final weighted + penalized reliability score
def calculate_reliability_score(scores: dict) -> dict:
    ''' applies tiered weights, critical ceiling, and major penalty to produce the final reliability score '''

    # FLOW-1: compute base weighted sum in all checks
    weighted = sum(
        scores[key] * RELIABILITY_TIERS[key]["weight"]
        for key in scores
    )

    # FLOW-2: you cannot go above 45 if any critical check failed. You can't have a 90 overall score when you sandbox failed completely.
    for key, meta in RELIABILITY_TIERS.items():
        if meta["tier"] == "critical" and scores[key] < 40:
            weighted = min(weighted, 45)    # USE: hard ceiling — critical failure caps the whole score

    # FLOW-3: apply 20% penalty for each major check that failed
    for key, meta in RELIABILITY_TIERS.items():
        if meta["tier"] == "major" and scores[key] < 40:
            weighted *= 0.80                # USE: each failing major check stacks a 20% penalty

    final_score = round(weighted, 2)

    # FLOW-4: build the breakdown so the caller knows per-check results
    breakdown = {
        key: {
            "score": scores[key],
            "tier": RELIABILITY_TIERS[key]["tier"],
            "weight": RELIABILITY_TIERS[key]["weight"],
        }
        for key in scores
    }

    return {
        "score": final_score,
        "label": get_risk_label(final_score),
        "breakdown": breakdown,
    }
# =========== FUNCTION ===========
