# WHAT DOES THIS FILE DO: Decides whether the pipeline should attempt another repair, and gives a status message for it.


# =========== FUNCTION ===========
# ROLE: single source of truth for "should we repair again" — pipeline just calls this instead of repeating the checks itself
def should_retry(confidence_score: float, repair_attempts: int, max_attempts: int) -> bool:
    ''' says no if attempts are used up, no if the score is already acceptable, yes otherwise '''

    # FLOW-1: attempts are capped, once we hit the ceiling there's nothing left to do but stop
    if repair_attempts >= max_attempts:
        return False

    # FLOW-2: score of 40+ is not great but it's not the "must repair" bucket either
    if confidence_score >= 40:
        return False

    return True
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: gives a short human-readable status for whichever stage of the repair loop we're currently in
def get_retry_message(repair_attempts: int, max_attempts: int) -> str:
    ''' picks the wording based on how many attempts have run so far vs the max allowed '''

    # FLOW-1: attempt 0 means we haven't repaired yet, this is the very first time the score came back low
    if repair_attempts == 0:
        return "Initial analysis complete. Quality score < 40. Auto-repairing..."

    # FLOW-2: still under the cap, this attempt is one of the retries
    if repair_attempts < max_attempts:
        return f"Repair attempt {repair_attempts}/{max_attempts}..."

    # FLOW-3: cap reached and score still bad — nothing more the loop can do
    return f"Max repair attempts ({max_attempts}) reached. Manual review recommended."
# =========== FUNCTION ===========
