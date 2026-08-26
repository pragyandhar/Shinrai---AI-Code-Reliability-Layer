# Shinrai — AI Code Reliability Layer
### Architecture & API Design Document
> Version: 1.2 | Stack: FastAPI + Celery + Redis + SQLite → AWS | LLM: Azure AI Foundry (GPT-4o)

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Pipeline Flow](#3-pipeline-flow)
4. [Component Breakdown](#4-component-breakdown)
   - 4.1 Code Reliability Mechanism
   - 4.2 Code Security Mechanism
   - 4.3 Confidence Scoring Mechanism
5. [Scoring Design](#5-scoring-design)
6. [Shinrai Output](#6-shinrai-output)
7. [API Design](#7-api-design)
8. [Project Structure](#8-project-structure)
9. [Tech Stack](#9-tech-stack)
10. [Future Scope](#10-future-scope)

---

## 1. Project Overview

**Shinrai** (信頼 — Japanese for *Trust/Reliability*) is a production-grade AI Code Reliability Layer that validates, scores, and audits LLM-generated code before it reaches production.

### Core Problem
LLMs like GPT-4o (via Azure AI Foundry) generate code that *looks* correct but may have runtime failures, security vulnerabilities, hallucinated imports, or logical inconsistencies. Shinrai provides a structured post-generation validation pipeline to surface these issues with actionable scores and reports.

### Key Capabilities
- Automated reliability analysis of LLM-generated Python code
- Security vulnerability scanning and secret detection
- Confidence scoring with tiered severity classification
- Modular API — full pipeline or standalone layer analysis
- Async task processing with real-time status polling
- Auto-repair loop for low-confidence code (max 3 retries)
- **Final output includes both detailed report AND production-ready fixed code**

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT / FRONTEND                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────────┐
│                     FASTAPI APPLICATION                         │
│                                                                 │
│   POST /generate          POST /analyze/reliability             │
│   POST /analyze/security  GET  /report/{task_id}                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Enqueue Task
┌──────────────────────────▼──────────────────────────────────────┐
│                     CELERY + REDIS                              │
│                    (Async Task Queue)                           │
└───────────┬───────────────────────────────┬─────────────────────┘
            │                               │
┌───────────▼────────────┐   ┌──────────────▼──────────────────┐
│  RELIABILITY WORKER    │   │      SECURITY WORKER            │
│  (Parallel Execution)  │   │      (Parallel Execution)       │
│                        │   │                                 │
│  1. Linting (Ruff)     │   │  1. SAST (Bandit)               │
│  2. Static Typing      │   │  2. CVE Check (pip-audit)       │
│  3. Hallucination Check│   │  3. Secret Detection            │
│  4. Sandbox Execution  │   │  4. Dangerous Pattern Scan      │
│  5. Auto Test Gen+Run  │   │  5. Security Score              │
│  6. Logic Flow (AST)   │   └──────────────┬──────────────────┘
│  7. Documentation Gen  │                  │
│  8. Reliability Score  │                  │
└───────────┬────────────┘                  │
            │                               │
            └──────────────┬────────────────┘
                           │ Both complete (Celery Chord)
┌──────────────────────────▼──────────────────────────────────────┐
│                  CONFIDENCE AGGREGATOR                          │
│         Weakest Link scoring on top of both scores              │
│         Risk Labels + Actionable Issue Report                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                  SQLITE DATABASE                                │
│          Stores: task_id, code, scores, report, status          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Pipeline Flow

```
User submits prompt
        │
        ▼
POST /generate
        │
        ▼
GPT-4o generates full code
        │
        ▼
Celery task enqueued
        │
        ├──────────────────────────────┐
        ▼                              ▼
[Reliability Worker]          [Security Worker]
  (async, parallel)            (async, parallel)
        │                              │
        └──────────────┬───────────────┘
                       ▼
              Celery Chord triggers
                       │
                       ▼
          [Confidence Aggregator]
                       │
                       ▼
            Score < 40 anywhere?
            ┌────────────────────┐
            │  YES               │  NO
            ▼                    ▼
     Auto-Repair Loop       [Code Fixer]
     (Max 3 retries)        GPT-4o repairs code
     Re-prompt GPT-4o       based on all issues
     with issue context          │
            │                    ▼
            │              Re-run full checks
            │              on fixed code
            │                    │
            └────────────────────┘
                       │
                       ▼
              Score >= 85? → "Production Ready" ✅
              Score 40-84? → "Fixed but review recommended" ⚠️
              Score < 40 after 3 retries? → "Manual review required" 🔴
                       │
                       ▼
                 Save to SQLite
                 status: "completed"
                       │
                       ▼
              GET /report/{task_id}
              (Report + Fixed Code + Diff)
```

---

## 4. Component Breakdown

### 4.1 Code Reliability Mechanism

| Step | Check | Tool | Severity Tier |
|------|-------|------|---------------|
| 1 | Code Structure — Linting | Ruff / Pylint | LOW |
| 2 | Static Type Checking | Mypy | HIGH |
| 3 | AI Hallucination Check — Import validation + API signature verification | Custom AST | CRITICAL |
| 4 | Sandbox Execution — Isolated run, runtime error capture | subprocess + resource limits (Dev) / Docker (Prod) | CRITICAL |
| 5 | Automatic Test Generation + Execution | Azure AI Foundry generated tests + pytest | HIGH |
| 6 | Logic Flow Analysis — Break of logic detection | AST-based analyzer | HIGH |
| 7 | Documentation Generation — Working vs failing functions | Auto-generated | — |
| 8 | Reliability Score | Tiered Scoring Algorithm | — |

---

### 4.2 Code Security Mechanism

| Step | Check | Tool | Severity Tier |
|------|-------|------|---------------|
| 1 | Static Security Analysis (SAST) — Known vulnerability patterns | Bandit | MAJOR |
| 2 | Dependency Vulnerability Check — CVEs in imported libraries | pip-audit | MINOR |
| 3 | Secret & Credential Detection — Hardcoded API keys, passwords, tokens | detect-secrets | CRITICAL |
| 4 | Sandbox Escape Detection — Dangerous patterns (os.system, subprocess, socket) | Custom AST rules | CRITICAL |
| 5 | Security Score | Tiered Scoring Algorithm | — |

---

### 4.3 Confidence Scoring Mechanism

Aggregates Reliability Score and Security Score into a final output with risk labels and actionable suggestions.

```
Reliability Score  →  Tiered Scoring
Security Score     →  Tiered Scoring
Overall Confidence →  Weakest Link on top of both scores
```

#### Tier Classification

**Reliability Tiers:**
| Tier | Checks |
|------|--------|
| CRITICAL | Sandbox Execution, AI Hallucination Check |
| HIGH | Static Typing, Auto Test Generation, Logic Flow Analysis |
| LOW | Linting |

**Security Tiers:**
| Tier | Checks |
|------|--------|
| CRITICAL | Secret Detection, Sandbox Escape Detection |
| MAJOR | SAST (Bandit) |
| MINOR | CVE Check |

---

## 5. Scoring Design

### Tiered Scoring Algorithm

```python
# Rules:
# CRITICAL check fails (score < 40) → hard ceiling at 45
# MAJOR check fails (score < 40)    → 20% penalty applied
# MINOR check fails                 → small weighted impact only

def tiered_score(scores: dict, tiers: dict) -> float:
    weighted = sum(scores[k] * tiers[k]["weight"] for k in scores)

    for k, meta in tiers.items():
        if meta["tier"] == "critical" and scores[k] < 40:
            weighted = min(weighted, 45)       # Hard ceiling

    for k, meta in tiers.items():
        if meta["tier"] == "major" and scores[k] < 40:
            weighted *= 0.80                   # 20% penalty

    return round(weighted, 2)
```

### Weakest Link — Overall Confidence

```python
def calculate_confidence(reliability: float, security: float) -> float:
    base = (reliability * 0.5) + (security * 0.5)
    min_score = min(reliability, security)

    if min_score < 40:
        penalty = (40 - min_score) * 0.5
        base -= penalty

    return round(max(0, base), 2)
```

### Risk Labels

| Score Range | Label | Status |
|-------------|-------|--------|
| 85 – 100 | Production Ready | 🟢 |
| 65 – 84 | Needs Minor Fixes | 🟡 |
| 40 – 64 | Significant Issues | 🟠 |
| 0 – 39 | Not Safe to Deploy | 🔴 |

---

## 6. Shinrai Output

Shinrai ka final output **sirf report nahi hai** — ek complete package hai jisme report bhi hai aur production-ready fixed code bhi.

### What Shinrai Returns

```
Shinrai Final Output
├── Original Generated Code          ← GPT-4o ka raw output
├── Reliability Report
│   ├── Score + Risk Label
│   └── Breakdown with tier-wise issues
├── Security Report
│   ├── Score + Risk Label
│   └── Breakdown with tier-wise issues
├── Confidence Score + Risk Label
├── Actionable Issues List           ← line number, severity, fix suggestion
├── Fixed Code                       ← GPT-4o repaired version
│   ├── What was changed (diff)
│   └── Repair attempt number (1, 2, or 3)
└── Final Scores after fix           ← re-run checks on fixed code
```

### Output States

| State | Condition | Message |
|-------|-----------|---------|
| ✅ Production Ready | Final score ≥ 85 | Safe to deploy |
| ⚠️ Fixed — Review Recommended | Score 40–84 after fix | Improvements made, manual review suggested |
| 🔴 Manual Review Required | Score < 40 after 3 retries | Shinrai could not auto-fix — human intervention needed |

### Guardrail — Fixed Code is Also Validated

Fixed code ko directly output **nahi** kiya jaata. Repair ke baad **same full pipeline dobara run** hoti hai fixed code pe. Tabhi final score assign hota hai.

```
Original Code → Checks → Issues Found → GPT-4o Fix → Re-run Checks → Final Output
```

---

## 7. API Design

### Base URL
```
http://localhost:8000/api/v1
```

---

### POST `/generate`
Triggers the full pipeline — code generation + reliability + security + confidence scoring.

**Request:**
```json
{
  "prompt": "Write a FastAPI CRUD app for a user management system"
}
```

**Response:**
```json
{
  "task_id": "abc-123-xyz",
  "status": "queued"
}
```

---

### POST `/analyze/reliability`
Standalone reliability analysis — submit any existing code directly.

**Request:**
```json
{
  "code": "def add(a, b):\n    return a + b"
}
```

**Response:**
```json
{
  "task_id": "rel-456-xyz",
  "status": "queued"
}
```

---

### POST `/analyze/security`
Standalone security analysis — submit any existing code directly.

**Request:**
```json
{
  "code": "import os\nos.system('rm -rf /')"
}
```

**Response:**
```json
{
  "task_id": "sec-789-xyz",
  "status": "queued"
}
```

---

### GET `/report/{task_id}`
Fetch the full analysis report.

**Response:**
```json
{
  "task_id": "abc-123-xyz",
  "status": "completed",
  "original_code": "...",
  "reliability": {
    "score": 78,
    "label": "Needs Minor Fixes",
    "breakdown": {
      "linting":           { "score": 90, "tier": "LOW" },
      "static_typing":     { "score": 70, "tier": "HIGH" },
      "hallucination":     { "score": 85, "tier": "CRITICAL" },
      "sandbox_execution": { "score": 60, "tier": "CRITICAL" },
      "test_generation":   { "score": 75, "tier": "HIGH" },
      "logic_flow":        { "score": 80, "tier": "HIGH" }
    }
  },
  "security": {
    "score": 65,
    "label": "Significant Issues",
    "breakdown": {
      "sast":               { "score": 80, "tier": "MAJOR" },
      "cve_check":          { "score": 90, "tier": "MINOR" },
      "secret_detection":   { "score": 100, "tier": "CRITICAL" },
      "dangerous_patterns": { "score": 30, "tier": "CRITICAL" }
    }
  },
  "confidence": {
    "score": 58,
    "label": "Significant Issues",
    "issues": [
      {
        "layer": "security",
        "type": "Dangerous Pattern",
        "line": 42,
        "detail": "os.system() detected — use subprocess with shell=False",
        "severity": "HIGH"
      }
    ]
  },
  "fixed_code": {
    "code": "...",
    "diff": "...",
    "repair_attempt": 1
  },
  "final_scores": {
    "reliability": { "score": 91, "label": "Production Ready" },
    "security":    { "score": 88, "label": "Production Ready" },
    "confidence":  { "score": 89, "label": "Production Ready" }
  },
  "output_state": "Production Ready",
  "documentation": "..."
}
```

---

### GET `/report/{task_id}/reliability`
Fetch only the reliability portion of the report.

---

### GET `/report/{task_id}/security`
Fetch only the security portion of the report.

---

### API Summary Table

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Full pipeline — generate + analyze |
| POST | `/analyze/reliability` | Standalone reliability check |
| POST | `/analyze/security` | Standalone security check |
| GET | `/report/{task_id}` | Full analysis report |
| GET | `/report/{task_id}/reliability` | Reliability report only |
| GET | `/report/{task_id}/security` | Security report only |

---

## 8. Project Structure

```
shinrai/
│
├── app/
│   ├── main.py                        # FastAPI entry point
│   ├── config.py                      # Settings, env vars, sandbox mode flag
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── generate.py            # POST /generate
│   │       ├── analyze.py             # POST /analyze/reliability, /analyze/security
│   │       └── report.py              # GET /report/{task_id}
│   │
│   ├── core/
│   │   ├── llm/
│   │   │   └── generator.py           # Azure AI Foundry (AzureOpenAI SDK) integration
│   │   │
│   │   ├── reliability/
│   │   │   ├── linter.py              # Ruff/Pylint
│   │   │   ├── type_checker.py        # Mypy
│   │   │   ├── hallucination.py       # Import + API signature check
│   │   │   ├── sandbox.py             # Isolated execution
│   │   │   ├── test_generator.py      # Azure AI Foundry test gen + pytest runner
│   │   │   ├── flow_analyzer.py       # AST logic flow
│   │   │   ├── doc_generator.py       # Documentation generation
│   │   │   └── scorer.py              # Tiered scoring
│   │   │
│   │   ├── security/
│   │   │   ├── sast.py                # Bandit
│   │   │   ├── cve_checker.py         # pip-audit
│   │   │   ├── secret_detector.py     # detect-secrets
│   │   │   ├── pattern_scanner.py     # AST dangerous patterns
│   │   │   └── scorer.py              # Tiered scoring
│   │   │
│   │   └── confidence/
│   │       └── aggregator.py          # Final score + labels + issues
│   │
│   ├── tasks/
│   │   ├── pipeline.py                # Full pipeline Celery task
│   │   ├── reliability_task.py        # Standalone reliability task
│   │   └── security_task.py           # Standalone security task
│   │
│   ├── models/
│   │   └── db.py                      # SQLite models (SQLAlchemy)
│   │
│   └── schemas/
│       └── report.py                  # Pydantic schemas
│
├── celery_worker.py                   # Celery app instance
├── docker-compose.yml                 # Redis + App
├── requirements.txt
├── .env
└── README.md
```

---

## 9. Tech Stack

| Layer | Technology |
|-------|------------|
| Web Framework | FastAPI |
| Async Task Queue | Celery |
| Message Broker | Redis |
| Database (Dev) | SQLite via SQLAlchemy |
| Database (Prod) | AWS RDS / DynamoDB |
| LLM Provider | Azure AI Foundry |
| LLM Model | GPT-4o (via AzureOpenAI SDK) |
| Linting | Ruff / Pylint |
| Static Typing | Mypy |
| Security SAST | Bandit |
| CVE Scanning | pip-audit |
| Secret Detection | detect-secrets |
| AST Analysis | Python `ast` module |
| Sandbox (Dev) | subprocess + resource limits |
| Sandbox (Prod) | Docker-in-Docker |
| Containerization | Docker + Docker Compose |

---

## 10. Future Scope

| Feature | Description | Version |
|---------|-------------|---------|
| Streaming Generation | Inline validation during code generation | V2 |
| Multi-language Support | JavaScript, Go, Java support | V2 |
| GitHub Integration | PR-level code validation webhook | V2 |
| VS Code Extension | Real-time Shinrai analysis in editor | V3 |
| Dashboard UI | Visual score history and trend analysis | V2 |
| Custom Rule Engine | User-defined reliability/security rules | V3 |

---

*Shinrai — Trust the code you ship.*
