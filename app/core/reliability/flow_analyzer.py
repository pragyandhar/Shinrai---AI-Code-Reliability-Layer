# WHAT DOES THIS FILE DO: Walks the AST of generated code and detects logic flow issues like unreachable code, empty excepts, etc.

# ================== IMPORTS ==================
import ast
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: finds functions that are defined in the code but never called anywhere
def _check_uncalled_functions(tree: ast.AST) -> list:
    ''' collects all function names and all call sites, returns names that appear in defs but not in calls '''

    defined = set()
    called = set()

    # FLOW-1: collect all function definition names
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(node.name)

    # FLOW-2: collect all simple function call names (e.g. foo(), not obj.foo())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called.add(node.func.id)

    uncalled = defined - called

    return [
        {"type": "uncalled_function", "detail": f"function '{name}' is defined but never called"}
        for name in uncalled
    ]
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: finds statements that appear after a return inside a function body — they will never execute
def _check_unreachable_code(tree: ast.AST) -> list:
    ''' walks each function body line by line, flags anything after a return at the same level '''

    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # FLOW-1: scan statements in the function body for a return
        found_return = False
        for stmt in node.body:
            if found_return:
                issues.append({
                    "type": "unreachable_code",
                    "line": stmt.lineno,
                    "detail": f"unreachable statement in '{node.name}' after return",
                })

            if isinstance(stmt, ast.Return):
                found_return = True

    return issues
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: finds except blocks that silently swallow errors — bare except or except with just pass
def _check_empty_except(tree: ast.AST) -> list:
    ''' looks for ExceptHandler nodes that are bare or have only a pass body '''

    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue

        # FLOW-1: bare except: with no exception type is too broad
        if node.type is None:
            issues.append({
                "type": "bare_except",
                "line": node.lineno,
                "detail": "bare 'except:' catches everything — use a specific exception type",
            })
            continue

        # FLOW-2: except block that only has pass silently swallows the error
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            issues.append({
                "type": "empty_except",
                "line": node.lineno,
                "detail": "except block only has 'pass' — error is silently swallowed",
            })

    return issues
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: detects while True loops that have no break — potential infinite loop
def _check_infinite_loops(tree: ast.AST) -> list:
    ''' finds while True loops and checks if a break exists anywhere inside the body '''

    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue

        # FLOW-1: check if the condition is literally True
        is_true = (
            isinstance(node.test, ast.Constant) and node.test.value is True
        )
        if not is_true:
            continue

        # FLOW-2: check if a break exists anywhere inside the loop body
        has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
        if not has_break:
            issues.append({
                "type": "infinite_loop",
                "line": node.lineno,
                "detail": "while True loop has no break — potential infinite loop",
            })

    return issues
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: finds functions that return values on some paths but not all — missing return on at least one path
def _check_missing_return(tree: ast.AST) -> list:
    ''' flags functions that have a return with a value but dont end with a return statement '''

    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # FLOW-1: check if the function has any return with an actual value
        has_value_return = any(
            isinstance(n, ast.Return) and n.value is not None
            for n in ast.walk(node)
        )
        if not has_value_return:
            continue

        # FLOW-2: if last statement in the body is not a return — some path falls off without returning
        last_stmt = node.body[-1]
        if not isinstance(last_stmt, ast.Return):
            issues.append({
                "type": "missing_return",
                "line": node.lineno,
                "detail": f"function '{node.name}' may not return a value on all paths",
            })

    return issues
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: runs all flow checks on the code string and returns a score + collected issues
def analyze_flow(code: str) -> dict:
    ''' parses code into AST, runs all five flow checks, returns score and issues list '''

    # FLOW-1: parse code — if syntax is broken none of the checks can run
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "score": 0,
            "tier": "HIGH",
            "issues": [{"type": "syntax_error", "detail": f"cannot parse code: {e}"}],
        }

    # FLOW-2: run all checks and combine issues into one list
    issues = []
    issues += _check_uncalled_functions(tree)
    issues += _check_unreachable_code(tree)
    issues += _check_empty_except(tree)
    issues += _check_infinite_loops(tree)
    issues += _check_missing_return(tree)

    # FLOW-3: score — start at 100, deduct 10 per issue, floor at 0
    score = max(0, 100 - (len(issues) * 10))

    return {
        "score": score,
        "tier": "HIGH",
        "issues": issues,
    }
# =========== FUNCTION ===========
