# WHAT DOES THIS FILE DO: Maps a confidence score to its risk label, color, emoji and deploy flag.


# =========== FUNCTION ===========
# ROLE: turns a 0-100 confidence score into the label info the rest of the app displays
def get_risk_label(score: float) -> dict:
    ''' picks the bucket the score falls in and returns label + color + emoji + deploy flag for it '''

    # FLOW-1: 85 and above is the only bucket safe to auto deploy
    if score >= 85:
        return {
            "label": "Production Ready",
            "color": "green",
            "emoji": "🟢",
            "deploy": True,
        }

    # FLOW-2: 65-84 still works but somebody should look at it before shipping
    if score >= 65:
        return {
            "label": "Needs Minor Fixes",
            "color": "yellow",
            "emoji": "🟡",
            "deploy": False,
        }

    # FLOW-3: 40-64 means real problems, not just nitpicks
    if score >= 40:
        return {
            "label": "Significant Issues",
            "color": "orange",
            "emoji": "🟠",
            "deploy": False,
        }

    # FLOW-4: anything below 40 is the bucket that triggers the repair loop
    return {
        "label": "Not Safe to Deploy",
        "color": "red",
        "emoji": "🔴",
        "deploy": False,
    }
# =========== FUNCTION ===========
