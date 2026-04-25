# AURA: Hiring and Capacity Decision Intelligence

AURA is a workforce planning and decision-support platform.

It combines team data, allocation data, budget constraints, and AI-assisted scenario analysis to answer practical planning questions such as:

- Where do we have staffing risk right now?
- What is the impact of delaying a hire?
- Which hiring sequence reduces risk most under budget limits?
- How likely is a knowledge transfer to succeed before planned exits?

## Product Positioning

This project is intentionally positioned as a decision layer, not only as a dashboard.

- AURA is the platform (data + workflows + reporting)
- AURORA is the AI reasoning engine inside AURA

Target direction: evolve from internal workforce planning to ATS-adjacent hiring intelligence.

## Why This Matters

Most organizations make hiring and staffing decisions across separate systems (recruiting, delivery, finance).
That creates blind spots.

AURA focuses on connecting those signals so decisions are:

- faster
- explainable
- measurable
- constrained by real budget and capacity limits

## Current Scope

### Functional Areas

1. Executive Dashboard
2. Master Data Management
3. Project Allocation Management
4. Financial Management
5. AI Scenario Analysis

### AI Scenario Types

1. Hiring delay impact
2. Employee addition impact
3. Component risk analysis
4. Hiring priority recommendation
5. Knowledge transfer success prediction
6. Custom free-form strategic questions

## Architecture Overview

The codebase follows a layered structure:

- Presentation Layer: Streamlit pages and dashboard UX
- Logic Layer: business services and scenario reasoning
- Data Access Layer: repository-style persistence APIs
- Persistence Layer: SQLite schema and state tables

Core directories:

- app.py
- pages/
- logic/
- database/
- ui/
- tests/

## Engineering Status (April 2026)

### What is already in place

- Modular service and repository structure
- SQLite-backed persistence for key app state
- Unit tests for core logic modules
- CI workflow for automated test execution
- Environment-based secret handling for API keys

### Known gaps before production-grade maturity

- AI output robustness and strict schema enforcement
- Broader test coverage (integration + scenario-level tests)
- API-first integration layer for external systems
- Stronger observability and auditability
- Multi-user and role-based access patterns

## ATS-Aligned Roadmap Direction

To align with the quality bar of companies like Ashby, the next milestones are:

1. Documentation and narrative consistency (single source of truth)
2. ATS-native domain model extensions (jobs, candidates, stages, interviews, offers)
3. AI hardening (validation, fallbacks, evaluation harness)
4. API contracts for integration-ready decision services
5. Decision quality metrics (time-to-fill, risk reduction, load balancing)

## Quick Start

### Prerequisites

- Python 3.12+
- Groq API key

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "GROQ_API_KEY=gsk_YOUR_KEY_HERE" > .env
streamlit run app.py
```

Open http://localhost:8501.

## Tests

Run unit tests:

```bash
pytest -q tests
```

## Additional Project Docs

- AURA_PROJECT_ANALYSIS.md
- AURA_ARCHITECTURE_DIAGRAMS.md
- AI_EXPERIMENT.md

## Notes

This repository is an active refactoring effort and is intended to show product thinking, engineering structure, and practical AI decision-support patterns in a real planning domain.
