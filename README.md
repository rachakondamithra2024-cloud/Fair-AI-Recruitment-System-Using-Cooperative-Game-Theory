# Fair AI Recruitment System Using Cooperative Game Theory
## Person C — Aggregation Engine & Integration Lead

This repository contains the central decision engine and integration harness for the Fair AI Recruitment System. Built on Cooperative Game Theory principles (Multi-Agent Nash Bargaining Solution and exact Shapley Value attributions), this module aggregates preferences from four specialized domain agents to render fair, resilient, and mathematically sound hiring decisions with zero LLM runtime dependency.

---

## 1. System Architecture

```
                                +-------------------------------+
                                | Candidate Profile & Job Desc  |
                                +---------------+---------------+
                                                |
                                                v
                                +---------------+---------------+
                                |      Integration Harness      |
                                +---------------+---------------+
                                                |
                     +------------------+-------+-------+------------------+
                     |                  |               |                  |
                     v                  v               v                  v
              +--------------+   +--------------+ +--------------+  +--------------+
              | Skills Agent |   | Experience   | | Diversity    |  | Economic     |
              | (Agent 1)    |   | Agent        | | Agent        |  | Agent        |
              +------+-------+   +------+-------+ +------+-------+  +------+-------+
                     |                  |               |                  |
                     +------------------+-------+-------+------------------+
                                                | (Outputs checked vs Contract v1.0.0)
                                                v
                                +---------------+---------------+
                                |  Contract v1.0.0 Validator &  |
                                |   Resilient Fallback Manager  |
                                +---------------+---------------+
                                                |
                                                v
                                +---------------+---------------+
                                |    Nash Bargaining Engine     |
                                |   (Hire vs Reject Surplus)    |
                                +---------------+---------------+
                                                |
                                                v
                                +---------------+---------------+
                                |     Shapley Value Module      |
                                |  (Per-Candidate Explanation & |
                                |   Offline Weight Calibration) |
                                +---------------+---------------+
                                                |
                                                v
                                +---------------+---------------+
                                |   Final Structured Decision   |
                                |     & Quantitative Report     |
                                +-------------------------------+
```

---

## 2. Core Components

### 2.1 Interface Contract (Section 0) — `docs/contract_v1.0.0.md` & `src/contract.py`
- Version: `1.0.0`
- Defines strict schema requirements for domain agents: `utility_hire`, `utility_reject`, `disagreement_point`, `weight`, `status`, `reasoning`.
- **Resilient Fallback Manager**: Automatically catches agent timeouts, runtime exceptions, missing fields, or out-of-bounds values, substituting safe disagreement point baselines (`status = FALLBACK`) without crashing the system.

### 2.2 Nash Bargaining Engine — `src/engine.py`
- Evaluates candidate surplus over disagreement thresholds $d_i$:
  $$G_i(D) = \max(U_i(D) - d_i, \epsilon), \quad \epsilon = 10^{-6}$$
- Computes weighted Nash Bargaining Product in log space for numerical stability:
  $$\ln N(D) = \sum_{i \in N} w_i \ln G_i(D), \quad \text{where } D \in \{\text{hire}, \text{reject}\}$$
- Decision rule: HIRE if $\ln N(\text{hire}) > \ln N(\text{reject})$ else REJECT.

### 2.3 Shapley Value Module — `src/shapley.py`
- Exact $N=4$ calculation ($2^4 = 16$ coalition subsets).
- Satisfies all fundamental game theory axioms: **Efficiency** ($\sum \phi_i = v(N)$), **Symmetry**, **Dummy Player** ($\phi_i = 0$ for neutral agents), and **Additivity**.
- **Online Mode**: Generates per-candidate quantitative feature attribution breakdowns highlighting each agent's percentage contribution to the outcome.
- **Offline Mode**: Calibrates default agent negotiation weights $w_i$ across historical validation datasets to equalize committee influence.

### 2.4 Integration Harness — `src/harness.py`
- Single unified interface wiring candidate inputs through domain agents, contract validation, Nash bargaining, and Shapley explainer to produce a clean `DecisionResult` dataclass.

### 2.5 Mock Agents & Stubs — `src/mocks.py`
- Standard mocks: `SkillsAgent`, `ExperienceAgent`, `DiversityAgent`, `EconomicAgent`.
- Fault injection stubs: `FaultyTimeoutAgent`, `FaultyMalformedAgent`, `FaultyExceptionAgent`.

---

## 3. Quick Start & Execution

### 3.1 Run Demo Script
```bash
py demo.py
```

### 3.2 Run Complete Test Suite
```bash
py run_tests.py
```

---

## 4. Usage Example

```python
from src import CandidateProfile, IntegrationHarness

# Define Candidate Profile
candidate = CandidateProfile(
    candidate_id="CAND-001",
    resume_text="Experienced Python & ML Developer...",
    job_description="Senior AI Engineer...",
    target_budget=125000.0,
    salary_expectation=120000.0,
    attributes={"skills": ["python", "machine_learning"], "years_experience": 5}
)

# Instantiate Integration Harness
harness = IntegrationHarness()

# Evaluate Candidate
result = harness.evaluate_candidate(candidate)

print(f"Decision: {result.decision}")
print(f"Explanation:\n{result.explanation}")
```

---

## 5. Directory Structure

```
.
├── docs/
│   └── contract_v1.0.0.md      # Interface Contract Specification (Section 0)
├── src/
│   ├── __init__.py             # Package Exports
│   ├── contract.py             # Data models & Contract Validation / Fallback
│   ├── engine.py               # Pure Nash Bargaining Decision Engine
│   ├── shapley.py              # Exact Shapley Value Explainer & Calibrator
│   ├── harness.py              # Integration Harness
│   └── mocks.py                # Realistic Mock Agents & Fault Injection Stubs
├── tests/
│   ├── test_contract.py        # Unit tests for Contract Validation & Fallbacks
│   ├── test_engine.py          # Unit tests for Nash Bargaining Math & Log Stability
│   ├── test_shapley.py         # Unit tests for Shapley Axioms & Explanations
│   └── test_harness.py        # End-to-End Integration Tests
├── demo.py                     # Interactive Demo Execution Script
├── run_tests.py                # Standalone Test Suite Runner
└── README.md                   # System Documentation
```
