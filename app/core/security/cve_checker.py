# WHAT DOES THIS FILE DO: Extracts imported packages from code and checks them against known CVEs via pip-audit.

# ================== IMPORTS ==================
import ast
import json
import subprocess
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: walks the AST and pulls out top-level package names from every import statement
def extract_imports(code: str) -> list:
    ''' parses the code, collects import + from-import module names, returns just the base package '''

    # FLOW-1: broken code can't be parsed at all, nothing to check
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    packages = set()

    # FLOW-2: walk every node, pull the base package off both import styles (e.g. "requests.auth" -> "requests")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                pkg = alias.name.split(".")[0]
                packages.add(pkg)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                pkg = node.module.split(".")[0]
                packages.add(pkg)

    return list(packages)
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: turns pip-audit's high/medium counts into a single 0-100 score
def calculate_cve_score(high: int, medium: int) -> float:
    ''' any fixable CVE (high) tanks the score, unfixable ones (medium) hurt less but still matter '''

    if high > 0:
        return 20

    if medium > 0:
        return 55

    return 100
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: runs pip-audit against the code's imports and returns score + CVE issues
def run_cve_check(code: str) -> dict:
    ''' extracts imports, feeds them to pip-audit as a requirements list, parses the CVEs it finds '''

    try:
        # FLOW-1: no imports means nothing to check — clean score, skip the subprocess call entirely
        imports = extract_imports(code)

        if not imports:
            return {
                "score": 100,
                "tier": "MINOR",
                "issues": [],
                "summary": {"total_cves": 0},
            }

        # FLOW-2: pip-audit takes a requirements-style list piped in via stdin
        requirements = "\n".join(imports)

        result = subprocess.run(
            ["pip-audit", "--format", "json", "--requirement", "-"],
            input=requirements,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = json.loads(result.stdout) if result.stdout else {}
        vulnerabilities = output.get("vulnerabilities", [])

        # FLOW-3: a fix being available is treated as the more urgent bucket — it means the CVE is confirmed and actionable
        high_cves = len([v for v in vulnerabilities if v.get("fix_available")])
        medium_cves = len([v for v in vulnerabilities if not v.get("fix_available")])

        score = calculate_cve_score(high_cves, medium_cves)

        issues = [
            {
                "type": "CVE Found",
                "package": v["name"],
                "cve_id": v.get("vulnerability_id"),
                "severity": "HIGH" if v.get("fix_available") else "MEDIUM",
                "detail": v.get("description"),
                "fix_available": v.get("fix_available"),
            }
            for v in vulnerabilities
        ]

        return {
            "score": score,
            "tier": "MINOR",
            "issues": issues,
            "summary": {"total_cves": len(vulnerabilities)},
        }

    except subprocess.TimeoutExpired:
        return {"score": 80, "tier": "MINOR", "issues": [], "error": "CVE check timeout"}

    except Exception as e:
        # USE: covers pip-audit not being installed (FileNotFoundError) and any bad/unparseable output
        return {"score": 80, "tier": "MINOR", "issues": [], "error": str(e)}
# =========== FUNCTION ===========
