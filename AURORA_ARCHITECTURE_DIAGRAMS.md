# 🏗️ AURORA: Architecture Diagrams & Visual Analysis

This document contains detailed architecture diagrams for the AURORA system.

---

## 1. SYSTEM ARCHITECTURE (3-Layer Model)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                              │
│                      (Streamlit Web UI)                             │
│                                                                      │
│  ┌──────────────┬──────────────┬─────────┬────────┬──────────────┐ │
│  │   Executive  │   Stammdaten │ Project │Budget  │ 🤖 AURORA   │ │
│  │  Dashboard   │  Management  │ Alloc.  │ Mgmt   │  Scenarios  │ │
│  │              │              │         │        │             │ │
│  │ • Team stats │ • Add/edit   │• Timeline│• Cost  │• Hiring     │ │
│  │ • KPIs       │ • Components │• Capacity│ charts │  delay      │ │
│  │ • Alerts     │ • Budgets    │• Gantt  │• Budget│• Employee   │ │
│  │              │              │         │        │  addition   │ │
│  └──────────────┴──────────────┴─────────┴────────┴──────────────┘ │
│                             △                                        │
│                    (State management                                 │
│                    via session_state)                               │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                      LOGIC LAYER                                    │
│                (Business Logic & Services)                          │
│                                                                      │
│  ┌──────────────┬──────────┬───────────┬─────────┬──────────────┐  │
│  │  AURORA      │  Team    │ Finance   │Allocation│Visualiz.   │  │
│  │  Engine      │ Service  │ Service   │Service   │Service     │  │
│  │              │          │           │          │            │  │
│  │ • Scenario   │• Compute │• Calc     │• Allocate│• Plotly    │  │
│  │   analysis   │  derived │  costs    │  capacity│ • Charts   │  │
│  │ • Multi-dim. │  fields  │• Budget   │• Validate│ • Gauges   │  │
│  │   impact     │• Priority│  forecasts│  utiliz. │ • Heatmaps │  │
│  │ • Reasoning  │• KT      │           │          │            │  │
│  │   prompts    │  status  │           │          │            │  │
│  └──────────────┴──────────┴───────────┴─────────┴──────────────┘  │
│                              △                                       │
│                     (Full data access,                              │
│                     query building)                                 │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                    DATA ACCESS LAYER                                │
│                   (Repository Pattern)                              │
│                                                                      │
│  ┌──────────────┬──────────────┬────────────┬──────────┬─────────┐ │
│  │    Team      │   Finance    │Allocation  │ Settings │ Session │ │
│  │ Repository   │ Repository   │Repository  │Resources │  Store  │ │
│  │              │              │            │          │        │ │
│  │ • Get members│ • Get budgets │• Get alloc │• Get    │• Persist│ │
│  │ • Add member │ • Set budgets │• Add alloc │  rates  │ • Load  │ │
│  │ • Update     │ • Calc costs  │• Check     │• Set    │  state  │ │
│  │ • Delete     │               │  capacity  │  rates  │        │ │
│  └──────────────┴──────────────┴────────────┴──────────┴─────────┘ │
│                              △                                       │
│                        (SQL queries                                 │
│                         to SQLite)                                  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                    PERSISTENCE LAYER                                │
│                   (SQLite Database)                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Tables:                                                      │  │
│  │  ├─ team_members (employees, roles, components)             │  │
│  │  ├─ budget_settings (cost per employee type)                │  │
│  │  ├─ employee_settings (individual rates)                    │  │
│  │  ├─ project_allocations (capacity assignments)              │  │
│  │  └─ app_config (application configuration)                  │  │
│  │                                                              │  │
│  │ File: ressourcenplanner.db (local SQLite file)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. AURORA ENGINE WORKFLOW

```
┌──────────────────────────────────────────────────────────────┐
│           USER INTERACTION                                  │
│  (Select scenario + Parameters)                             │
└──────────────────┬───────────────────────────────────────────┘
                   │
    ┌──────────────▼────────────────┐
    │ AURORA ENGINE INITIALIZATION  │
    │                               │
    │ • Load company context        │
    │ • Initialize Groq client      │
    │ • Prepare prompt templates    │
    └──────────────┬────────────────┘
                   │
    ┌──────────────▼────────────────────────────────┐
    │ DATA GATHERING & CONTEXT BUILDING             │
    │                                               │
    │ _build_context() {                            │
    │   • Query team_members table                  │
    │   • Query budget_settings table               │
    │   • Query project_allocations table           │
    │   • Calculate derived metrics                 │
    │   • Identify planned exits                    │
    │   • Assess component complexity               │
    │ }                                             │
    │                                               │
    │ Output: Rich context document (~500 tokens)   │
    └──────────────┬────────────────────────────────┘
                   │
    ┌──────────────▼────────────────────────────────┐
    │ PROMPT CONSTRUCTION                           │
    │                                               │
    │ Template: "You are an expert consultant..."   │
    │ + Context: (Company data)                     │
    │ + Scenario: (User's what-if question)         │
    │ + Instructions: (Analysis task)               │
    │ + Format: (JSON structure expected)           │
    │ + Constraints: (Domain rules)                 │
    │                                               │
    │ Output: Complete prompt (~2K tokens)          │
    └──────────────┬────────────────────────────────┘
                   │
    ┌──────────────▼────────────────────────────────┐
    │ LLM API CALL (Groq)                           │
    │                                               │
    │ POST /openai/v1/chat/completions {            │
    │   model: "llama-3.3-70b-versatile",           │
    │   messages: [prompts...],                     │
    │   max_tokens: 2000,                           │
    │   temperature: 0.7                            │
    │ }                                             │
    │                                               │
    │ Latency: 5-30 seconds typical                │
    └──────────────┬────────────────────────────────┘
                   │
    ┌──────────────▼────────────────────────────────┐
    │ RESPONSE PARSING                              │
    │                                               │
    │ • Extract JSON from response                  │
    │ • Validate JSON structure                     │
    │ • Type-check all fields                       │
    │ • Capture reasoning text                      │
    │ • Build ScenarioResult object                 │
    └──────────────┬────────────────────────────────┘
                   │
    ┌──────────────▼────────────────────────────────┐
    │ RESULT STORAGE                                │
    │                                               │
    │ st.session_state.scenario_results = {         │
    │   "scenario_type": "hiring_delay",            │
    │   "timeline_impact_days": 45,                 │
    │   "budget_impact_euros": 120000,              │
    │   "risk_increase_percent": 25,                │
    │   "recommendation": "RECONSIDER",             │
    │   "confidence_score": 82,                     │
    │   ...                                         │
    │ }                                             │
    └──────────────┬────────────────────────────────┘
                   │
    ┌──────────────▼────────────────────────────────┐
    │ UI RENDERING                                  │
    │                                               │
    │ • Display metrics (4-column layout)           │
    │ • Show AURORA Reasoning (expandable)          │
    │ • Generate visualizations                     │
    │ • Display recommendations                     │
    │ • Show alternatives                           │
    │ • Highlight key insights                      │
    └──────────────────────────────────────────────┘
```

---

## 3. DATA FLOW DIAGRAM

```
                    ┌──────────────────┐
                    │   Streamlit UI   │
                    │   (5 Pages)      │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼──────┐      ┌─────▼────┐       ┌──────▼──┐
   │Dashboard  │      │Dashboard │       │ AURORA  │
   │ Page      │      │ Logic    │       │ Engine  │
   │           │      │          │       │         │
   │ (Reads    │      │ Queries  │       │ (Reads) │
   │  reports)◄──────── repos   ◄────────── Repos
   │           │      │          │       │ & calls │
   └───────────┘      └────┬─────┘       │ Groq    │
                           │              └────┬────┘
                           │                   │
      ┌────────────────────┼───────────────────┘
      │                    │
      │    ┌───────────────▼─────────────────┐
      │    │    Repositories                 │
      │    │                                 │
      │    │ • team_repository               │
      │    │ • finance_repository            │
      │    │ • allocation_repository         │
      │    │ • settings_repository           │
      │    │ • session_store                 │
      │    └──────────────┬──────────────────┘
      │                   │
      │    ┌──────────────▼──────────────────┐
      │    │  SQL Layer                      │
      │    │                                 │
      │    │  SELECT * FROM team_members ... │
      │    │  WHERE ... ORDER BY ...         │
      │    └──────────────┬──────────────────┘
      │                   │
      └───────────────────┼──────────────────┐
                          │                  │
                    ┌─────▼────────┐  ┌──────▼──────┐
                    │ SQLite DB    │  │Groq API     │
                    │              │  │             │
                    │ Tables:      │  │ (External)  │
                    │ • team_m     │  │             │
                    │ • budget_s   │  │ LLM Model   │
                    │ • allocat_a  │  │ Reasoning   │
                    └──────────────┘  └─────────────┘
```

---

## 4. SCENARIO FLOWCHART (Example: Hiring Delay)

```
START (User selects "Hiring Delay" scenario)
│
├─ INPUT COLLECTION
│  ├─ Component name: "Backend Services"
│  ├─ Delay duration: "30 days"
│  ├─ Criticality: "important"
│  └─ Budget constraint: "€200,000"
│
├─ DATA GATHERING
│  ├─ Query: current team for "Backend Services"
│  │         Result: 3 people (need 5)
│  ├─ Query: component details
│  │         Result: 60-day KT needed
│  ├─ Query: planned exits in next 12 months
│  │         Result: 1 person leaving in 6 months
│  └─ Query: budget settings
│          Result: avg cost €4,500/person/month
│
├─ CONTEXT BUILDING
│  │
│  COMPONENT INFO:
│  ├─ Name: Backend Services
│  ├─ Criticality: important
│  ├─ Current staffing: 3/5 (60% capacity)
│  ├─ Staffing gap: 2 people
│  ├─ Responsible: Alice Schmidt, Bob Mueller
│  └─ KT time needed: 60 days
│  │
│  TEAM CONTEXT:
│  ├─ Total team: 15 people
│  ├─ Exits planned (12 mo): 1 person
│  ├─ Team capacity: 78% of target
│  └─ Recent hires: 2 in last 6 months
│  │
│  BUSINESS CONTEXT:
│  ├─ Industry: Siemens
│  ├─ Avg hiring time: 60-90 days
│  └─ Strategic importance: high
│
├─ PROMPT CONSTRUCTION
│  │
│  "You are an expert workforce consultant.
│   
│   COMPONENT: Backend Services
│   - Criticality: important
│   - Current: 3/5 staffing
│   - Gap: 2 people needed
│   - KT: 60 days required
│   
│   SCENARIO: Delay hiring by 30 days
│   
│   Predict: timeline, budget, risk impacts..."
│
├─ GROQ API CALL (llama-3.3-70b-versatile)
│  │
│  LLM Reasoning:
│  "If we delay 30 days:
│   - Hiring starts day 30 instead of day 0
│   - Person arrives day 90 (assuming 60 day process)
│   - KT takes additional 60 days
│   - Component will run understaffed for 150 days
│   - Risk: delayed feature delivery, higher burnout
│   - Budget: saves €9k (1 month salary deferred)
│   - BUT: risk is high given 1 person leaving soon"
│
├─ RESPONSE PARSING
│  │
│  LLM Output (JSON):
│  {
│    "timeline_impact_days": 45,
│    "budget_impact_euros": -9000,
│    "risk_increase_percent": 35,
│    "recommendation": "RECONSIDER",
│    "alternatives": [
│      {
│        "option": "Hire externally (contractor, faster",
│        "timeline_impact": 15,
│        "budget_impact": 20000,
│        "effectiveness": 90
│      }
│    ],
│    "confidence_score": 78
│  }
│
├─ RESULT STORAGE
│  └─ st.session_state.scenario_results ← result
│
├─ VISUALIZATION GENERATION
│  ├─ Chart 1: Timeline impact (45 days)
│  ├─ Chart 2: Budget gauge (-€9k saves)
│  ├─ Chart 3: Risk gauge (↑35% MEDIUM-HIGH)
│  └─ Chart 4: Confidence (78% HIGH)
│
└─ END (Display results to user)
```

---

## 5. DATABASE RELATIONSHIP DIAGRAM

```
┌─────────────────────────────────────────┐
│       DATABASE RELATIONSHIPS            │
└─────────────────────────────────────────┘

                team_members
                ┌─────────────────┐
                │ id (PK)         │
                │ name            │────────────┐
                │ role            │            │
                │ employee_type   │─┐          │
                │ components      │ │          │
                │ start_date      │ │          │
                │ planned_exit    │ │          │
                │ dob             │ │          │
                └─────────────────┘ │          │
                        ▲            │         │
                        │            │         │
                        │ FK         │ FK      │
                 1:N    │            │          │ Name (1:N)
                        │           ▼          │
              ┌─────────────────┐   ┌─────────────────────┐
              │budget_settings  │   │employee_settings    │
              ├─────────────────┤   ├─────────────────────┤
              │employee_type(PK)│   │employee_name (PK)   │
              │monthly_cost     │   │hourly_rate          │
              │yearly_budget    │   │weekly_hours         │
              │hourly_rate      │   └─────────────────────┘
              │weekly_hours     │
              └─────────────────┘

                project_allocations
                ┌─────────────────────────┐
                │ id (PK)                 │
                │ employee (FK) ◄─────────┼─── team_members.name
                │ project                 │
                │ start_date              │
                │ end_date                │
                │ percentage              │
                └─────────────────────────┘

                app_config
                ┌─────────────────────────┐
                │ key (PK)                │
                │ value_json (JSON)       │
                └─────────────────────────┘
```

**Key Relationships:**
- `team_members.employee_type` → `budget_settings.employee_type` (Many-to-One)
- `project_allocations.employee` → `team_members.name` (Many-to-One)
- `employee_settings` keyed by employee name for individual overrides

---

## 6. REQUEST/RESPONSE CYCLE

```
USER REQUEST CYCLE
│
├─ REQUEST (User actions in UI)
│  ├─ Click button: "Analyze Hiring Delay"
│  ├─ Select scenario parameters
│  │  ├─ Component: Backend
│  │  ├─ Delay: 30 days
│  │  └─ Criticality: important
│  │
│  └─ Streamlit detects change → Full rerun
│
├─ PROCESSING (Backend execution)
│  ├─ script_execution_context set
│  ├─ session_state retrieved from browser
│  ├─ Form values combined with stored state
│  │
│  ├─ Scenario method called:
│  │  aurora.simulate_hiring_delay(
│  │    component="Backend",
│  │    delay_days=30,
│  │    ...
│  │  )
│  │
│  ├─ Repositories execute SQL queries
│  │  ├─ SELECT * FROM team_members
│  │  ├─ SELECT * FROM budget_settings
│  │  └─ Results returned as Python dicts
│  │
│  ├─ AURORA engine builds context
│  │  ├─ Format data into text
│  │  ├─ Create specialized prompt
│  │  └─ Groq API call
│  │
│  ├─ Groq processes request
│  │  ├─ Tokenize prompt
│  │  ├─ Run LLM inference (llama-3.3-70b)
│  │  ├─ Generate response tokens
│  │  └─ Return as text
│  │
│  ├─ Parse response
│  │  ├─ Extract JSON
│  │  ├─ Validate structure
│  │  └─ Return ScenarioResult
│  │
│  └─ Store in session state
│     session_state.scenario_results = result
│
├─ RENDERING (UI generation)
│  ├─ Streamlit calls st.metric() for KPIs
│  ├─ Visualizations generated from results
│  │  ├─ Plotly chart functions called
│  │  └─ Charts rendered as HTML/JSON
│  │
│  ├─ Page re-rendered with all widgets
│  │  ├─ Form fields (with values)
│  │  ├─ Result metrics
│  │  ├─ Charts
│  │  └─ Recommendations
│  │
│  └─ HTML sent to browser
│
└─ RESPONSE (Browser display)
   ├─ Receives HTML/JSON/CSS
   ├─ Renders UI elements
   ├─ Displays charts via Plotly.js
   ├─ Streamlit JS handles interactions
   └─ User sees results

[On user interaction: Restart from REQUEST]
```

---

## 7. DEPLOYMENT ARCHITECTURE (Current vs Future)

### Current (Prototype)

```
LOCAL MACHINE (Developer)
│
├─ Python 3.12 + venv
├─ Streamlit (localhost:8501)
├─ SQLite (local file)
└─ .env with Groq API key
│
└─ streamlit run app.py
   └─ launches web server
      └─ user accesses via browser
```

### Future (Production)

```
CLOUD PROVIDER (AWS/GCP/Azure)
│
├─ Content Delivery Network (CDN)
│  └─ Static assets (React build, CSS, JS)
│
├─ Load Balancer
│  └─ Distributes traffic
│
├─ Kubernetes Cluster (App servers)
│  ├─ FastAPI container (Python)
│  ├─ Replica 1
│  ├─ Replica 2
│  ├─ Replica 3
│  └─ Auto-scaling based on CPU/memory
│
├─ Managed PostgreSQL Database
│  ├─ Primary instance
│  ├─ Replica instance (read-only)
│  ├─ Automated daily backups
│  └─ Point-in-time recovery
│
├─ Redis Cache Layer
│  ├─ Session storage
│  ├─ API response cache
│  └─ Rate limiting store
│
├─ Secrets Management (AWS Secrets Manager)
│  ├─ Groq API key (encrypted)
│  ├─ Database credentials
│  └─ JWT signing keys
│
├─ Monitoring & Observability
│  ├─ Prometheus (metrics)
│  ├─ Grafana (dashboards)
│  ├─ ELK Stack (logging)
│  ├─ Sentry (error tracking)
│  └─ DataDog (APM)
│
├─ S3 Storage (File storage)
│  ├─ Backups
│  ├─ Exports
│  └─ Logs
│
└─ CI/CD Pipeline (GitHub Actions)
   ├─ Run tests
   ├─ Build container
   ├─ Push to registry
   └─ Deploy to Kubernetes
```

---

## 8. COMPONENT INTERACTION DIAGRAM

```
┌────────────────────────────────────────────────────────────────┐
│                      COMPONENT INTERACTIONS                     │
└────────────────────────────────────────────────────────────────┘

          ┌─────────────────────┐
          │   Streamlit Pages   │
          └────────┬────────────┘
                   │
        ┌──────────┼──────────────┐
        │          │              │
   ┌────▼────┐ ┌──▼────────┐ ┌───▼─────────┐
   │Dashboard│ │Scenarios  │ │Data Mgmt    │
   │         │ │           │ │             │
   │ Calls   │ │ Calls     │ │ Calls       │
   │Services │ │AURORA     │ │Repository   │
   └─────────┘ └───────────┘ └─────────────┘
       │             │              │
       │             │              │
       └─────┬───────┴──────┬───────┘
             │              │
        ┌────▼────────┐  ┌──▼────────────────┐
        │  Services   │  │ AURORA Engine     │
        │             │  │                   │
        │ • Team      │  │ • scenario_engine │
        │ • Finance   │  │ • visualization   │
        │ • Allocat.  │  │ • prompt builder  │
        │             │  │                   │
        └────┬────────┘  └──────────┬────────┘
             │                      │
        ┌────▼───────────────────┬──▼──┐
        │ Repositories           │     │
        │                        │Groq │
        │ • team_repo            │API  │
        │ • finance_repo         │     │
        │ • allocation_repo      │     │
        └────┬────────────────────┴─────┘
             │
        ┌────▼──────────┐
        │  SQLite DB    │
        │               │
        │ • team_mem... │
        │ • budget_s... │
        │ • project_a.. │
        └───────────────┘
```

---

## 9. STATE MANAGEMENT FLOW

```
STREAMLIT SESSION STATE LIFECYCLE

1. INITIAL LOAD (Page refresh)
   ├─ Browser: POST request to Streamlit
   ├─ Server: Initialize empty session_state
   ├─ Server: Run script top to bottom
   ├─ Server: Render HTML
   ├─ Browser: Display page
   └─ State in memory for this tab

2. USER INTERACTION (Click button, type in form)
   ├─ Browser: Detects change
   ├─ Browser: Sends delta to Streamlit
   ├─ Server: Receives WebSocket message
   ├─ Server: Update session_state[key]
   ├─ Server: Re-run script (full execution)
   ├─ Server: Find widget states from session
   ├─ Server: Re-render HTML
   └─ Browser: Update DOM

3. SCENARIO EXECUTION
   ├─ Form values extracted: st.session_state
   ├─ AURORA engine called with form data
   ├─ Result stored: st.session_state.scenario_results
   ├─ st.rerun() called (force full re-execution)
   ├─ Result displayed in UI
   └─ State persists for navigation

4. NAVIGATION
   ├─ User clicks sidebar link
   ├─ URL changes
   ├─ Page reloads
   ├─ NEW session_state initialized (!!! State lost)
   ├─ Script runs from top
   └─ User sees initial state

5. PAGE REFRESH [BLOCKER]
   ├─ User hits F5
   ├─ Browser: Full page reload
   ├─ Server: session_state garbage collected
   ├─ Server: NEW session_state initialized
   ├─ Script: Re-runs from scratch
   ├─ UI: Reverts to initial state
   └─ Results lost ❌
```

---

## 10. AURORA DECISION TREE

```
                    Scenario Analysis Request
                            │
                ┌───────────┬┼┬───────────┐
                │           ││            │
         ┌──────▼──────┐    ││      ┌─────▼────────┐
         │Hiring Delay?│    ││      │Employee Add? │
         └──────┬──────┘    ││      └──────┬────────┘
                │YES        ││             │YES
         ┌──────▼──────────────┐          │
         │ Query component     │          │
         │ staffing level      │          │
         └──────┬──────────────┘          │
                │                ┌───────────▼────────┐
                │               │ Assess hiring date │
                │               │ vs project need    │
                │               └────────┬───────────┘
                │                        │
                │           ┌────────────▼──────────────┐
                │           │ Calculate timeline       │
                │           │ + Budget + Risk impact   │
                │           └────────┬─────────────────┘
                │                    │
                │      Recommendation Decision
                │                    │
         ┌──────┴───────────┬────────┴────────────────┐
         │                  │                         │
    ┌────▼────┐    ┌────────▼────────┐        ┌──────▼──────┐
    │EXECUTE  │    │ RECONSIDER      │        │HOLD/AVOID   │
    │         │    │                 │        │             │
    │Timing   │    │Impact too high  │        │Risk critical│
    │looks ok │    │or uncertain     │        │ or blocking │
    └─────────┘    └─────────────────┘        └─────────────┘
         │                  │                         │
         │                  │                         │
         └──────────────────┴─────────────────────────┘
                         │
                  ┌──────▼──────┐
                  │ Present to  │
                  │ User with   │
                  │ confidence  │
                  │ score       │
                  └─────────────┘
```

---

**Diagrams Version:** 1.0  
**Date:** April 1, 2026

