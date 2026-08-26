# WHAT DOES THIS FILE DO: Generates a human-readable diff between original and fixed code, plus stats on it.

# ================== IMPORTS ==================
import difflib
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: builds a unified diff string showing what changed between the two code versions
def generate_diff(original_code: str, fixed_code: str) -> str:
    ''' returns an empty string when nothing changed, otherwise a standard unified diff '''

    # FLOW-1: identical code means nothing to show — skip the diff entirely
    if original_code == fixed_code:
        return ""

    original_lines = original_code.splitlines(keepends=True)
    fixed_lines = fixed_code.splitlines(keepends=True)

    # FLOW-2: unified diff format, same layout as git diff
    diff_lines = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile="original.py",
        tofile="fixed.py",
        lineterm="",
    )

    return "\n".join(diff_lines)
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: counts added/removed lines out of a diff string, for a quick summary without re-reading the whole thing
def get_diff_stats(diff_text: str) -> dict:
    ''' counts lines starting with + or - — skips the +++ / --- file header lines implicitly since those start with two chars '''

    lines = diff_text.split("\n")
    added = len([l for l in lines if l.startswith("+") and not l.startswith("+++")])
    removed = len([l for l in lines if l.startswith("-") and not l.startswith("---")])

    return {
        "lines_added": added,
        "lines_removed": removed,
        "total_changes": added + removed,
    }
# =========== FUNCTION ===========
