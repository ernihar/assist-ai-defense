# MSI Assist AI — Defense Engineering Repository

A production-style, executable repository demonstrating hands-on AI security engineering: LLM guardrails, prompt injection detection, tool authorization, and adversarial evaluation — running fully **local** with Ollama + LangChain.

This repo prioritizes **working code over theory**. Every commit leaves the project in a runnable, testable state.

## Why This Repo Exists

- Runtime guardrail systems (input/output filters, prompt injection detection, content classification, tool-call authorization) — not slideware
- Adversarial evaluation without requiring GPU training
- Automated pytest coverage proving the guardrails actually work
- Clean separation of concerns and CI-ready structure

The running example is **MSI Assist AI**, a simulated emergency dispatch assistant, used consistently across every guardrail layer.

## Project Structure

```
assist-ai-defense/
├── app/
│   ├── llm/          # LLM client wrapper (Ollama + LangChain in later commits)
│   ├── guardrails/   # Input/output guardrails, schemas, reusable validators
│   ├── tools/        # Tool definitions the agent can call
│   ├── auth/         # Tool authorization (RBAC/ABAC-style access control)
│   ├── evaluation/   # Adversarial evaluation harness, baseline vs defended outputs
│   └── config/       # Centralized settings (.env driven)
├── tests/            # Pytest suite — one file per feature
├── data/             # Simulated adversarial datasets (no GPU training required)
├── prompts/          # System prompts and injection payloads used in tests
├── reports/          # Generated evaluation reports (gitignored)
├── scripts/          # CLI entry points (Rich-formatted output)
├── .github/workflows/ # CI pipeline
├── requirements.txt
├── pytest.ini
└── .env.example
```

## Tech Stack

| Layer | Tool |
|---|---|
| LLM runtime | Ollama (local `llama3.2`) |
| Orchestration | LangChain |
| Data validation | Pydantic |
| Testing | Pytest |
| Config | python-dotenv |
| CLI output | Rich |
| CI | GitHub Actions |

No cloud APIs, no GPU training required — everything runs on a normal laptop.

## Roadmap

| # | Module | Status |
|---|---|---|
| 1 | Project bootstrap & CI scaffold | Done |
| 2 | Character-based input validation (Pydantic guardrail) | Done |
| 2.5 | Pydantic design upgrade (cross-field validation + reusable validators) | Done |
| 3 | Content classification guardrail | Planned |
| 4 | Prompt injection detection (semantic layer) | Planned |
| 5 | Tool authorization (RBAC/ABAC) | Planned |
| 6 | Adversarial training simulation (no GPU) | Planned |
| 7 | Adversarial tuning simulation (no GPU) | Planned |
| 8 | Adversarial evaluation harness + reports | Planned |
| 9 | Ollama + LangChain agent integration | Planned |
| 10 | End-to-end skills assessment demo | Planned |

## Getting Started

```bash
git clone <your-repo-url> assist-ai-defense
cd assist-ai-defense

python3.11 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install --only-binary=:all: -r requirements.txt
cp .env.example .env

pytest
```

## Module 1: Project Bootstrap

Establishes the folder structure, `.env`-driven settings loader, pytest harness, and CI workflow every later module builds on.

- **What problem does it solve?** A runnable, CI-ready skeleton so guardrail features have a consistent home and test harness from day one.
- **Where is the guardrail?** None yet — pure scaffolding.
- **How is it tested?** `tests/test_project_bootstrap.py`.
- **Which file contains the implementation?** `app/config/settings.py`.

## Module 2: Character-Based Validation (Input Guardrail)

A dispatcher submits a free-text incident request. Before it reaches the LLM, the request must pass a structural and character-whitelist check.

| Field | Validation | Example |
|---|---|---|
| incident_id | `^INC-\d{4}$` | `INC-2045` |
| grid | `^[A-Z0-9]{2,4}$` | `5B`, `A12` |
| priority | `LOW` \| `MEDIUM` \| `HIGH` | `HIGH` |
| description | whitelist regex, 1–500 chars | `Shots fired near Central Mall` |

`protected_query_llm()` in `app/guardrails/pipeline.py` validates first and only calls `query_llm()` if validation succeeds — fail-closed by design.

- **Known limitation:** character validation checks format, not meaning. "Ignore previous instructions..." passes this layer because it uses only whitelisted characters — this is why a semantic guardrail layer comes later.

## Module 2.5: Pydantic Design Upgrade

**Why this upgrade exists:** Commit 2's validation worked, but it had two real gaps that a QA-architecture-minded interviewer would notice immediately: the whitelist check was glued to one class (not reusable), and no rule could ever check two fields together.

**What changed:**

1. **Reusable validator function** — `app/guardrails/validators.py` now holds `validate_operational_characters()` as a plain function, attached to the `description` field via `Annotated[str, AfterValidator(...)]` instead of a class-bound `@field_validator`. Any future schema can reuse this exact function.
2. **Cross-field validation** — a `@model_validator(mode="after")` on `DispatchRequest` now enforces: if `priority == "HIGH"`, `description` must be at least 10 characters. This is a rule no single `field_validator` could express, since it depends on two fields at once.
3. **Structured error reporting** — `GuardrailRejection.as_field_errors()` converts Pydantic's raw `ValidationError` into a simple `[{"field": ..., "message": ...}]` list, including a safe fallback (`"request"`) for model-level cross-field errors that have no single field attached.

- **Where is the guardrail?** `app/guardrails/validators.py` (reusable check), `app/guardrails/schemas.py` (cross-field rule), `app/guardrails/pipeline.py` (structured errors).
- **How is it tested?** `tests/test_cross_field_validation.py` — 10 new tests across three classes, one per upgrade. `tests/test_character_validation.py` is kept behaviorally identical to Commit 2 as a regression check.
- **Interview framing:** "I started with per-field validation. Once I needed a rule spanning two fields — HIGH priority requiring a real description — I added a `model_validator`, which runs after all individual fields pass. I also extracted the character check into a standalone function so future schemas don't duplicate it, and gave the rejection exception a method that returns clean, structured errors instead of raw Pydantic internals."

## License

MIT
