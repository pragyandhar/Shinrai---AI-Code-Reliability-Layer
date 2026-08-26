# WHAT DOES THIS FILE DO: Walks the AST of generated code and flags calls to known dangerous functions.

# ================== IMPORTS ==================
import ast
# ================== IMPORTS ==================


# =========== VARIABLES : dangerous call name -> severity + fix suggestion ===========
DANGEROUS_PATTERNS = {
    "os.system": {"severity": "CRITICAL", "suggestion": "Use subprocess.run with shell=False"},
    "subprocess.call": {"severity": "CRITICAL", "suggestion": "Use subprocess.run instead"},
    "subprocess.Popen": {"severity": "CRITICAL", "suggestion": "Use subprocess.run for safer execution"},
    "__import__": {"severity": "CRITICAL", "suggestion": "Use importlib instead of __import__"},
    "eval": {"severity": "CRITICAL", "suggestion": "Avoid eval() — use ast.literal_eval for safe parsing"},
    "exec": {"severity": "CRITICAL", "suggestion": "Avoid exec() — use importlib or subprocess"},
    "open": {"severity": "HIGH", "suggestion": "Validate file paths to prevent directory traversal"},
    "socket.connect": {"severity": "HIGH", "suggestion": "Validate URLs and implement connection timeouts"},
}
# =========== VARIABLES : dangerous call name -> severity + fix suggestion ===========


# =========== FUNCTION ===========
# ROLE: AST visitor that walks every function call in the tree and checks it against the dangerous pattern list
class DangerousPatternVisitor(ast.NodeVisitor):
    ''' collects one issue per call node that matches something in DANGEROUS_PATTERNS '''

    def __init__(self):
        self.issues = []

    # FLOW-1: every Call node in the tree passes through here
    def visit_Call(self, node):
        ''' resolves the call's full name (e.g. "os.system") then checks it against every known pattern '''

        func_name = self.get_full_name(node.func)

        for pattern, info in DANGEROUS_PATTERNS.items():
            if func_name and pattern in func_name:
                self.issues.append({
                    "line": node.lineno,
                    "pattern": pattern,
                    "severity": info["severity"],
                    "suggestion": info["suggestion"],
                })

        self.generic_visit(node)     # USE: keeps walking into nested calls, e.g. foo(os.system(...))

    # FLOW-2: turns a Name node ("open") or an Attribute chain ("os.system") into one dotted string
    @staticmethod
    def get_full_name(node):
        ''' recurses down Attribute nodes to build the dotted name, returns None for anything else '''

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            value = DangerousPatternVisitor.get_full_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr

        return None
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: turns the visitor's flagged issues into a single 0-100 score
def calculate_pattern_score(critical: int, high: int) -> float:
    ''' one CRITICAL call already tanks the score badly, two or more zeroes it out '''

    if critical == 0 and high == 0:
        return 100

    if critical == 0:
        return 60

    if critical == 1:
        return 20

    return 0
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: parses the code, runs the dangerous-pattern visitor over it, returns score + flagged calls
def run_pattern_scanner(code: str) -> dict:
    ''' walks the AST looking for calls to eval, exec, os.system and friends '''

    try:
        tree = ast.parse(code)
        visitor = DangerousPatternVisitor()
        visitor.visit(tree)

        issues = visitor.issues
        critical_count = len([i for i in issues if i["severity"] == "CRITICAL"])
        high_count = len([i for i in issues if i["severity"] == "HIGH"])

        score = calculate_pattern_score(critical_count, high_count)

        return {
            "score": score,
            "tier": "CRITICAL",
            "issues": issues,
            "summary": {
                "critical": critical_count,
                "high": high_count,
            },
        }

    except SyntaxError as e:
        return {
            "score": 50,
            "tier": "CRITICAL",
            "issues": [],
            "error": f"Syntax error: {str(e)}",
        }

    except Exception as e:
        return {
            "score": 50,
            "tier": "CRITICAL",
            "issues": [],
            "error": str(e),
        }
# =========== FUNCTION ===========
