# AURA: Automated Resource Analytics

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

## Key Features

**Real-time AI Analysis** - Get insights in seconds, not weeks  
**Multi-dimensional Impact** - Timeline + Budget + Risk assessment  
**Transparent Reasoning** - See why AURORA recommends something  
**Confidence Scoring** - Know how certain the AI is (0-100%)  
**Alternative Suggestions** - Explore different approaches  
**Interactive Visualizations** - Plotly charts for insights  
**German Localization** - Native language support  

## Business Value

- AI output robustness and strict schema enforcement
- Broader test coverage (integration + scenario-level tests)
- API-first integration layer for external systems
- Stronger observability and auditability
- Multi-user and role-based access patterns

## ATS-Aligned Roadmap Direction

To take the project to enterprise level, the next milestones are:

1. Documentation and narrative consistency (single source of truth)
2. ATS-native domain model extensions (jobs, candidates, stages, interviews, offers)
3. AI hardening (validation, fallbacks, evaluation harness)
4. API contracts for integration-ready decision services
5. Decision quality metrics (time-to-fill, risk reduction, load balancing)

```
ressourcenplanner/
├── app.py                          # Main AURA dashboard
├── pages/
│   ├── Stammdaten_Management.py   # Team management
│   ├── Projekt_Allocation.py      # Project allocation
│   ├── Finanzielle_Verwaltung.py # Budget management
│   └── Scenario_Analysis.py       # AURORA scenarios
├── logic/
│   ├── scenario_engine.py         # AURORA AI engine
│   ├── team_service.py            # Team logic
│   ├── finance_service.py         # Finance logic
│   ├── allocation_service.py      # Allocation logic
│   └── visualization_service.py   # Chart generation
├── database/
│   ├── connection.py              # SQLite connection
│   ├── schema.py                  # Database schema
│   ├── team_repository.py         # Team data access
│   ├── finance_repository.py      # Finance data access
│   ├── allocation_repository.py   # Allocation data access
│   └── session_store.py           # State persistence
├── ui/
│   └── theme.py                   # Streamlit theming
├── .env                           # Configuration (add Groq API key)

└── requirements.txt               # Python dependencies
```

### Prerequisites

- API keys stored in `.env` (not in version control)
- `.env` added to `.gitignore`
- No hardcoded secrets
- Groq API key validated on startup (Note : The models will be trained on Siemens accelerator platform)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "GROQ_API_KEY=gsk_YOUR_KEY_HERE" > .env
streamlit run app.py
```

**For Production:**
- Logic layer (reusable)
- Frontend (Streamlit → React migration needed)
- Database (SQLite → PostgreSQL scaling needed)
- Testing (add comprehensive test coverage)

## Tests

Run unit tests:

```bash
pytest -q tests
```

## Contact & Support

- AURA_PROJECT_ANALYSIS.md
- AURA_ARCHITECTURE_DIAGRAMS.md
- AI_EXPERIMENT.md

## Notes

This repository is an active refactoring effort and is intended to show product thinking, engineering structure, and practical AI decision-support patterns in a real planning domain.
