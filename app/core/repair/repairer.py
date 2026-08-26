# WHAT DOES THIS FILE DO: Builds a repair prompt from actionable issues and sends it back to GPT-4o to fix the code.

# ================== IMPORTS ==================
from app.core.llm.generator import generate_code
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: turns the actionable issues list + the broken code into one structured prompt for GPT-4o
def create_repair_prompt(original_code: str, actionable_issues: list) -> str:
    ''' lists every issue with its severity and line, then hands GPT-4o the original code to fix around it '''

    # FLOW-1: one line per issue so GPT-4o sees exactly what's wrong and where — not every issue has a line number (hallucination, sandbox), so we skip that part instead of printing "Line None"
    issues_text = "\n".join(
        f"- [{issue['severity']}] Line {issue['line']}: {issue['detail']}" if issue["line"] is not None
        else f"- [{issue['severity']}] {issue['detail']}"
        for issue in actionable_issues
    )

    # FLOW-2: the prompt keeps it strict — issues first, code second, then a hard rule to return code only
    prompt = f"""You are a Python code repair expert. Fix the following code based on these issues:

ISSUES TO FIX:
{issues_text}

ORIGINAL CODE:
```python
{original_code}
```

REQUIREMENTS:
1. Fix all listed issues
2. Keep the same functionality
3. Return ONLY the repaired code, no explanations
4. Ensure code is production-ready

REPAIRED CODE:
"""

    return prompt
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: sends the repair prompt to GPT-4o and hands back the repaired code
def repair_code(original_code: str, actionable_issues: list) -> str:
    ''' builds the repair prompt then reuses the same generator the pipeline uses for the initial code generation '''

    # FLOW-1: build the prompt from the code and the issues found on it
    prompt = create_repair_prompt(original_code, actionable_issues)

    # FLOW-2: generate_code already strips markdown/whitespace, no need to repeat that here
    repaired = generate_code(prompt)

    return repaired
# =========== FUNCTION ===========
