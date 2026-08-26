# Phase 4 — Security Layer
> Static security analysis, CVE scanning, secret detection, dangerous patterns

---

## Table of Contents
1. [Overview](#1-overview)
2. [Files to Build](#2-files-to-build)
3. [Security Flow](#3-security-flow)
4. [File Breakdown](#4-file-breakdown)
5. [Scoring Strategy](#5-scoring-strategy)
6. [Integration Points](#6-integration-points)
7. [Error Handling](#7-error-handling)

---

## 1. Overview

Security Layer runs **4 parallel checks** on generated code:

1. **SAST** — Bandit static security analysis
2. **CVE Check** — pip-audit for vulnerable dependencies
3. **Secret Detection** — Hardcoded API keys, passwords, tokens
4. **Pattern Scanner** — AST-based dangerous function detection

Output: Individual scores → Tiered Scoring → Final Security Score

---

## 2. Files to Build

```
app/core/security/
├── sast.py             # Bandit integration
├── cve_checker.py      # pip-audit integration
├── secret_detector.py  # Hardcoded secrets detection
├── pattern_scanner.py  # Dangerous patterns via AST
├── scorer.py           # Tiered security scoring
└── runner.py           # Orchestrator
```

**Update:**
- `app/tasks/pipeline.py` — call security runner

---

## 3. Security Flow

```
Generated Code
        │
        ├──────────────────────────────┐
        ▼                              ▼
   [SAST via Bandit]           [CVE Check via pip-audit]
   Parse vulnerabilities       Extract imports + check CVEs
        │                              │
        └──────────────┬───────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
  [Secret Detector]          [Pattern Scanner]
  Regex/detect-secrets       AST dangerous calls
        │                             │
        └──────────────┬──────────────┘
                       │
                       ▼
            [Tiered Security Scorer]
            Combine 4 scores with tiers
                       │
                       ▼
            security_score (0-100)
            + breakdown (per-check scores)
            + issues list
```

---

## 4. File Breakdown

### File 1 — `app/core/security/sast.py`

**Kaam:** Bandit se code mein vulnerability patterns detect karo

```python
import subprocess
import json
import tempfile

def run_sast(code: str) -> dict:
    """
    Run Bandit on code via stdin
    Returns: score (0-100), issues list
    """
    
    try:
        # Run bandit on stdin with JSON output
        result = subprocess.run(
            ["bandit", "-f", "json", "-"],
            input=code,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse JSON output
        output = json.loads(result.stdout)
        results = output.get("results", [])
        
        # Count by severity
        high_count = len([r for r in results if r["severity"] == "HIGH"])
        medium_count = len([r for r in results if r["severity"] == "MEDIUM"])
        low_count = len([r for r in results if r["severity"] == "LOW"])
        
        # Scoring logic
        score = calculate_sast_score(high_count, medium_count, low_count)
        
        # Format issues
        issues = [
            {
                "type": "SAST Vulnerability",
                "line": r.get("line_number"),
                "severity": r["severity"],
                "detail": r.get("issue_text"),
                "test_id": r.get("test_id")
            }
            for r in results
        ]
        
        return {
            "score": score,
            "tier": "MAJOR",
            "issues": issues,
            "summary": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            }
        }
        
    except subprocess.TimeoutExpired:
        return {"score": 20, "tier": "MAJOR", "issues": [], "error": "SAST timeout"}
    except Exception as e:
        return {"score": 20, "tier": "MAJOR", "issues": [], "error": str(e)}


def calculate_sast_score(high: int, medium: int, low: int) -> float:
    """
    Scoring logic:
    - 0 issues → 100
    - LOW only → 80
    - MEDIUM present → 55
    - HIGH present → 20
    """
    
    if high > 0:
        return 20
    elif medium > 0:
        return 55
    elif low > 0:
        return 80
    else:
        return 100
```

---

### File 2 — `app/core/security/cve_checker.py`

**Kaam:** Code ke imports mein known CVEs check karo via pip-audit

```python
import subprocess
import ast
import json

def extract_imports(code: str) -> list:
    """
    Parse code AST and extract all imported packages
    Returns: ["requests", "pandas", "numpy", ...]
    """
    
    try:
        tree = ast.parse(code)
        packages = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Extract base package name
                    pkg = alias.name.split(".")[0]
                    packages.add(pkg)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    packages.add(pkg)
        
        return list(packages)
        
    except SyntaxError:
        return []


def run_cve_check(code: str) -> dict:
    """
    Run pip-audit on extracted imports
    Returns: score (0-100), CVE issues
    """
    
    try:
        imports = extract_imports(code)
        
        if not imports:
            return {
                "score": 100,
                "tier": "MINOR",
                "issues": [],
                "summary": {"total_cves": 0}
            }
        
        # Create requirements string
        requirements = "\n".join(imports)
        
        # Run pip-audit
        result = subprocess.run(
            ["pip-audit", "--format", "json", "--requirement", "-"],
            input=requirements,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = json.loads(result.stdout) if result.stdout else {}
        vulnerabilities = output.get("vulnerabilities", [])
        
        # Count by severity
        high_cves = len([v for v in vulnerabilities if v.get("fix_available")])
        medium_cves = len([v for v in vulnerabilities if not v.get("fix_available")])
        
        # Score
        score = calculate_cve_score(high_cves, medium_cves)
        
        # Format issues
        issues = [
            {
                "type": "CVE Found",
                "package": v["name"],
                "cve_id": v.get("vulnerability_id"),
                "severity": v.get("fix_available") and "HIGH" or "MEDIUM",
                "detail": v.get("description"),
                "fix_available": v.get("fix_available")
            }
            for v in vulnerabilities
        ]
        
        return {
            "score": score,
            "tier": "MINOR",
            "issues": issues,
            "summary": {"total_cves": len(vulnerabilities)}
        }
        
    except subprocess.TimeoutExpired:
        return {"score": 80, "tier": "MINOR", "issues": [], "error": "CVE check timeout"}
    except Exception as e:
        return {"score": 80, "tier": "MINOR", "issues": [], "error": str(e)}


def calculate_cve_score(high: int, medium: int) -> float:
    """
    Scoring logic:
    - 0 CVEs → 100
    - 1 CVE (LOW) → 80
    - 1+ CVE (MEDIUM) → 55
    - 1+ CVE (HIGH) → 20
    """
    
    if high > 0:
        return 20
    elif medium > 0:
        return 55
    elif high == 0 and medium == 0:
        if (high + medium) == 1:
            return 80
    
    return 100
```

---

### File 3 — `app/core/security/secret_detector.py`

**Kaam:** Hardcoded API keys, passwords, tokens detect karo

```python
import re
import subprocess
import json

# Regex patterns for common secrets
SECRET_PATTERNS = {
    "api_key": r"['\"]?[a-zA-Z_][a-zA-Z0-9_]*['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9\-_]{20,})['\"]",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "github_token": r"ghp_[a-zA-Z0-9_]{36,}",
    "private_key": r"-----BEGIN (RSA|DSA|EC|PGP|OPENSSH) PRIVATE KEY-----",
    "password": r"['\"]?password['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
    "secret": r"['\"]?secret['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
}


def run_secret_detector(code: str) -> dict:
    """
    Detect hardcoded secrets in code
    Returns: score (0-100), detected secrets
    """
    
    secrets_found = []
    
    # Line-by-line check
    for line_num, line in enumerate(code.split("\n"), 1):
        # Skip comments
        if line.strip().startswith("#"):
            continue
        
        # Check each pattern
        for secret_type, pattern in SECRET_PATTERNS.items():
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                secrets_found.append({
                    "type": secret_type,
                    "line": line_num,
                    "detail": f"Hardcoded {secret_type} detected",
                    "masked_value": line[:20] + "..."
                })
    
    # Scoring
    score = calculate_secret_score(len(secrets_found))
    
    return {
        "score": score,
        "tier": "CRITICAL",
        "issues": secrets_found,
        "summary": {"total_secrets": len(secrets_found)}
    }


def calculate_secret_score(count: int) -> float:
    """
    Scoring logic:
    - 0 secrets → 100
    - 1 secret → 30
    - 2+ secrets → 0
    """
    
    if count == 0:
        return 100
    elif count == 1:
        return 30
    else:
        return 0
```

---

### File 4 — `app/core/security/pattern_scanner.py`

**Kaam:** AST se dangerous function calls detect karo

```python
import ast

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


class DangerousPatternVisitor(ast.NodeVisitor):
    """AST visitor to find dangerous function calls"""
    
    def __init__(self):
        self.issues = []
    
    def visit_Call(self, node):
        """Visit function call nodes"""
        
        # Get full function name
        func_name = self.get_full_name(node.func)
        
        # Check against dangerous patterns
        for pattern, info in DANGEROUS_PATTERNS.items():
            if func_name and pattern in func_name:
                self.issues.append({
                    "line": node.lineno,
                    "pattern": pattern,
                    "severity": info["severity"],
                    "suggestion": info["suggestion"]
                })
        
        self.generic_visit(node)
    
    @staticmethod
    def get_full_name(node):
        """Extract full function name from AST node"""
        
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = DangerousPatternVisitor.get_full_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        
        return None


def run_pattern_scanner(code: str) -> dict:
    """
    Scan for dangerous patterns via AST
    Returns: score (0-100), flagged patterns
    """
    
    try:
        tree = ast.parse(code)
        visitor = DangerousPatternVisitor()
        visitor.visit(tree)
        
        issues = visitor.issues
        
        # Separate by severity
        critical_count = len([i for i in issues if i["severity"] == "CRITICAL"])
        high_count = len([i for i in issues if i["severity"] == "HIGH"])
        
        # Scoring
        score = calculate_pattern_score(critical_count, high_count)
        
        return {
            "score": score,
            "tier": "CRITICAL",
            "issues": issues,
            "summary": {
                "critical": critical_count,
                "high": high_count
            }
        }
        
    except SyntaxError as e:
        return {
            "score": 50,
            "tier": "CRITICAL",
            "issues": [],
            "error": f"Syntax error: {str(e)}"
        }
    except Exception as e:
        return {
            "score": 50,
            "tier": "CRITICAL",
            "issues": [],
            "error": str(e)
        }


def calculate_pattern_score(critical: int, high: int) -> float:
    """
    Scoring logic:
    - 0 patterns → 100
    - HIGH only → 60
    - 1 CRITICAL → 20
    - 2+ CRITICAL → 0
    """
    
    if critical == 0 and high == 0:
        return 100
    elif critical == 0 and high > 0:
        return 60
    elif critical == 1:
        return 20
    else:
        return 0
```

---

### File 5 — `app/core/security/scorer.py`

**Kaam:** Tiered scoring — 4 checks combine karo final security score mein

```python
def calculate_security_score(
    sast_score: float,
    cve_score: float,
    secret_score: float,
    pattern_score: float
) -> float:
    """
    Tiered Security Scoring
    
    Tiers:
    - CRITICAL: secret_detector, pattern_scanner
    - MAJOR: sast
    - MINOR: cve_checker
    """
    
    SECURITY_TIERS = {
        "secret_detector": {"score": secret_score, "weight": 0.30, "tier": "critical"},
        "pattern_scanner": {"score": pattern_score, "weight": 0.30, "tier": "critical"},
        "sast": {"score": sast_score, "weight": 0.25, "tier": "major"},
        "cve_checker": {"score": cve_score, "weight": 0.15, "tier": "minor"},
    }
    
    # Calculate weighted base
    weighted = sum(
        item["score"] * item["weight"]
        for item in SECURITY_TIERS.values()
    )
    
    # Apply CRITICAL tier penalties
    for key, item in SECURITY_TIERS.items():
        if item["tier"] == "critical" and item["score"] < 40:
            weighted = min(weighted, 45)  # Hard ceiling
    
    # Apply MAJOR tier penalties
    for key, item in SECURITY_TIERS.items():
        if item["tier"] == "major" and item["score"] < 40:
            weighted *= 0.80  # 20% penalty
    
    return round(weighted, 2)


def build_security_breakdown(sast: dict, cve: dict, secret: dict, pattern: dict) -> dict:
    """
    Format all check results into breakdown structure
    """
    
    return {
        "sast": {
            "score": sast["score"],
            "tier": sast["tier"],
            "summary": sast.get("summary", {}),
            "issues": sast.get("issues", [])
        },
        "cve_check": {
            "score": cve["score"],
            "tier": cve["tier"],
            "summary": cve.get("summary", {}),
            "issues": cve.get("issues", [])
        },
        "secret_detection": {
            "score": secret["score"],
            "tier": secret["tier"],
            "summary": secret.get("summary", {}),
            "issues": secret.get("issues", [])
        },
        "dangerous_patterns": {
            "score": pattern["score"],
            "tier": pattern["tier"],
            "summary": pattern.get("summary", {}),
            "issues": pattern.get("issues", [])
        }
    }
```

---

### File 6 — `app/core/security/runner.py`

**Kaam:** Orchestrator — sab 4 checks run karo parallel, then aggregate

```python
from app.core.security.sast import run_sast
from app.core.security.cve_checker import run_cve_check
from app.core.security.secret_detector import run_secret_detector
from app.core.security.pattern_scanner import run_pattern_scanner
from app.core.security.scorer import calculate_security_score, build_security_breakdown


def run_security(code: str) -> dict:
    """
    Run all security checks
    Returns: complete security report
    """
    
    # Run all 4 checks (can be parallelized with threading/async)
    sast_result = run_sast(code)
    cve_result = run_cve_check(code)
    secret_result = run_secret_detector(code)
    pattern_result = run_pattern_scanner(code)
    
    # Calculate final score
    final_score = calculate_security_score(
        sast_result["score"],
        cve_result["score"],
        secret_result["score"],
        pattern_result["score"]
    )
    
    # Build breakdown
    breakdown = build_security_breakdown(
        sast_result,
        cve_result,
        secret_result,
        pattern_result
    )
    
    # Flatten all issues
    all_issues = [
        {**issue, "check": "sast"}
        for issue in sast_result.get("issues", [])
    ] + [
        {**issue, "check": "cve_checker"}
        for issue in cve_result.get("issues", [])
    ] + [
        {**issue, "check": "secret_detection"}
        for issue in secret_result.get("issues", [])
    ] + [
        {**issue, "check": "dangerous_patterns"}
        for issue in pattern_result.get("issues", [])
    ]
    
    return {
        "score": final_score,
        "breakdown": breakdown,
        "issues": all_issues,
        "total_issues": len(all_issues)
    }
```

---

## 5. Scoring Strategy

### Tiers

```
CRITICAL (weight 0.30 each):
  - secret_detector
  - pattern_scanner
  → If either < 40 → hard ceiling 45 on final score

MAJOR (weight 0.25):
  - sast
  → If < 40 → 20% penalty on final score

MINOR (weight 0.15):
  - cve_checker
  → Weighted impact only
```

### Example Scenarios

| Scenario | Scores | Final |
|----------|--------|-------|
| All good | [100, 100, 100, 100] | 100 |
| SAST issues | [40, 100, 100, 100] | ~94 (0.80 penalty) |
| Secret found | [100, 100, 30, 100] | 45 (ceiling) |
| Multiple CRITICAL | [80, 20, 30, 100] | 45 (ceiling + penalties) |

---

## 6. Integration Points

### Update `app/tasks/pipeline.py`

```python
from app.core.security.runner import run_security

@celery_app.task
def run_pipeline(task_id: str, prompt: str):
    
    # Step 1: Generate code
    generated_code = generate_code(prompt)
    
    # Step 2: Reliability checks
    reliability_report = run_reliability(generated_code)
    
    # Step 3: Security checks ← NEW
    security_report = run_security(generated_code)
    
    # Step 4-5: Confidence + repair (Phase 5)
    # ...
```

---

## 7. Error Handling

### Tool Not Installed
```python
try:
    result = subprocess.run(["bandit", ...])
except FileNotFoundError:
    # Tool missing → return safe default score
    return {"score": 50, "tier": "MAJOR", "error": "Bandit not installed"}
```

### Timeout
```python
except subprocess.TimeoutExpired:
    return {"score": 50, "tier": "MAJOR", "error": "Security check timeout"}
```

### Invalid Code
```python
except SyntaxError:
    # Can't parse AST → still run subprocess tools
    return {"score": 70, "tier": "CRITICAL", "warning": "Syntax error in code"}
```

---

## Summary

**6 new files:**

```
sast.py             ← Bandit SAST scanning
cve_checker.py      ← pip-audit CVE detection
secret_detector.py  ← Regex-based secret detection
pattern_scanner.py  ← AST dangerous patterns
scorer.py           ← Tiered security scoring
runner.py           ← Orchestrator
```

**Update:**
- `pipeline.py` — call security runner after reliability

---

## Git Commit Message

```
feat(phase-4): security layer with SAST, CVE check, secret detection, and pattern scanning

- Integrate Bandit for static security analysis with severity-based scoring
- Add pip-audit CVE vulnerability scanning on extracted imports
- Implement regex and pattern-based hardcoded secret detection
- Create AST-based dangerous function pattern scanner (os.system, eval, exec, etc)
- Build Tiered Security Scorer with CRITICAL/MAJOR/MINOR tiers and hard ceilings
- Add security runner orchestrator combining all 4 checks with parallel capability
- Update pipeline task to call security layer after reliability checks
```

---

*Shinrai — Phase 4 ready for implementation*