# WHAT DOES THIS FILE DO: Combines reliability + security reports into one final confidence report using weakest-link scoring.

# ================== IMPORTS ==================
from app.core.confidence.risk_labels import get_risk_label
from app.core.confidence.issue_formatter import format_issues
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: applies the weakest-link formula so one badly failing layer drags the whole score down, not just averages it away
def calculate_confidence(reliability_score: float, security_score: float) -> float:
    ''' takes the 50/50 average of both scores, then punishes it further if either score is under 40 '''

    # FLOW-1: start from a plain 50/50 average of the two layers
    base = (reliability_score * 0.5) + (security_score * 0.5)
    min_score = min(reliability_score, security_score)

    # FLOW-2: whichever layer is weakest decides if there's an extra penalty — average alone would hide a bad layer behind a good one
    if min_score < 40:
        penalty = (40 - min_score) * 0.5
        base -= penalty

    return round(max(0, base), 2)
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: builds the full confidence report the pipeline and the API report endpoint both rely on
def aggregate_report(reliability: dict, security: dict) -> dict:
    ''' combines both layer reports into one confidence score + label + issue list + repair flag '''

    # FLOW-1: get the single confidence number first — everything else is derived from it
    confidence_score = calculate_confidence(reliability["score"], security["score"])

    # FLOW-2: confidence score decides the label, issue list comes from both layers' breakdowns
    risk_label = get_risk_label(confidence_score)
    actionable_issues = format_issues(reliability, security)

    return {
        "confidence_score": confidence_score,
        "risk_label": risk_label["label"],
        "emoji": risk_label["emoji"],
        "deploy_safe": risk_label["deploy"],
        "issues": actionable_issues,
        "needs_repair": confidence_score < 40,     # USE: this flag is what tells the pipeline to enter the repair loop
    }
# =========== FUNCTION ===========
