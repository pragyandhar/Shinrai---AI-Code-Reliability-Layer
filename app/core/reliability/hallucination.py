# WHAT DOES THIS FILE DO: Checks if imports in LLM-generated code actually exist — flags hallucinated ones.

# ================== IMPORTS ==================
import ast
import importlib.util
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: walks through the AST and returns a flat list of top-level module names from all import statements
def extract_imports(tree: ast.AST) -> list[str]:
    ''' It pulls out module names from import and from-import statements, skips relative imports. We get the tree from ast.parse() command. '''

    modules = []

    # FLOW-1: walk every node in the AST and grab module names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            # FLOW-2: It skips relative imports — find_spec can't resolve them
            if node.level and node.level > 0:
                continue

            if node.module:
                modules.append(node.module)

    return modules
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: It checks each import in the code against the local environment, flags the ones that don't exist
def check_hallucinations(code: str) -> dict:
    ''' parses code, extracts imports, checks each with find_spec, returns score and hallucinated list '''

    # FLOW-1: parse the code - if syntax is broken we can't check imports at all
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "score": 0,
            "tier": "CRITICAL",
            "issues": [{"module": None, "message": f"syntax error — cannot parse code: {e}"}],
        }

    # FLOW-2: extract all import module names from the AST
    modules = extract_imports(tree)

    # FLOW-3: check each module — flag ones that find_spec can't locate
    hallucinated = []
    for module in modules:
        try:
            spec = importlib.util.find_spec(module)     # USE: It checks if the module you are searching for exists on your system or not? If not then it returns None else a ModuleSpec object
            if spec is None:
                hallucinated.append(module)
        except (ModuleNotFoundError, ValueError):       # USE: If there is wrong module name or if parent package is missing
            hallucinated.append(module)

    # FLOW-4: build issues list from hallucinated imports
    issues = [
        {"module": m, "message": f"import '{m}' could not be resolved — likely hallucinated"}
        for m in hallucinated
    ]

    # FLOW-5: score — start at 100, deduct 20 per hallucinated import, floor at 0
    score = max(0, 100 - (len(hallucinated) * 20))

    return {
        "score": score,
        "tier": "CRITICAL",
        "issues": issues,
    }
# =========== FUNCTION ===========