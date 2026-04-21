# 🤖 AURORA - Scenario Simulation Experiment

**Branch:** `aura-ai-prototype`  
**Status:** 🧪 Experimental - In Active Development  
**Created:** April 1, 2026

---

## 🎯 Vision

Transform ressourcenplanner from a **resource tracking tool** into an **AI-powered workforce optimization platform** that predicts the impact of management decisions.

**Key Question:** Instead of asking "What are our resources?", ask "What happens if...?"

---

## 💡 What This Does

### Available Scenarios

#### 1. **Hiring Delay Impact Simulator** ✅
```
"If we delay hiring for Component X by 60 days, what happens to our timeline and budget?"

Input:
  - Component to delay
  - Delay duration (days)
  - Component criticality

Output:
  - Predicted timeline delay
  - Budget impact (€)
  - Risk increase (%)
  - AI recommendation + alternatives
```

#### 2. **Employee Impact Analyzer** ✅
```
"What happens if we add Jane (Senior Dev) to our team?"

Input:
  - New employee details
  - Assigned components
  - Start date
  - Salary

Output:
  - Key risk reductions
  - Timeline improvements
  - Budget implications
  - Knock-on effects
  - Hire/No Hire recommendation
```

#### 3. **Component Risk Assessment** ✅
```
"How risky is Component X right now?"

Input:
  - Component name
  - Current vs required staffing

Output:
  - Risk score (0-100)
  - Single point of failure assessment
  - Months until critical
  - Priority hiring needed
  - Alternatives to hiring
```

#### 4. **Hiring Priority Optimizer** ✅
```
"We can hire 3 people with €180K. Which components first?"

Input:
  - Budget available
  - Max hires allowed

Output:
  - Optimal hiring sequence (by priority)
  - Cost breakdown
  - Risk reduction by sequence
  - Why this sequence wins
```

#### 5. **Knowledge Transfer Success Predictor** ✅
```
"Will the KT succeed if Alex leaves in 120 days?"

Input:
  - Departing person
  - KT duration (weeks)
  - Assigned replacement (optional)

Output:
  - Success probability
  - KT plan phases
  - Critical tasks
  - Budget for external help
  - Contingency if KT fails
```

---

## 🔧 Technical Stack

### AI Model
- **Groq - Mixtral 8x7B** (Free & Lightning Fast, but only used for exprimenting)
  - State-of-the-art open model
  - Perfect for business scenario analysis
  - **100% FREE** - no payment required
  - Ultra-fast inference (< 1 second)
- Final version will have custom trained models from Siemens internal platform- Siemens Xcelerator tom increase data safety and accurate decisions.

### Additional Libraries
```python
groq==0.9.0           # Groq API client
streamlit>=1.28.0     # Already included
pandas>=2.0.0         # Already included
plotly>=5.0.0         # Already included
```

---

## 🚀 How to Use

### Step 1: Get FREE API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up for free (takes 1 minute)
3. Copy your API key (starts with `gsk_`)

### Step 2: Set Environment Variable

```bash
# macOS/Linux
export GROQ_API_KEY=gsk-your-key-here

# Windows (PowerShell)
$env:GROQ_API_KEY='gsk-your-key-here'

# Or add to .env file (then load with python-dotenv)
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the App

```bash
streamlit run app.py
```

### Step 5: Navigate to Scenario Analysis

In the sidebar, click: **🤖 Scenario Analysis AI**

---

## 💰 Cost Estimation

### API Pricing (Anthropic Claude 3.5 Sonnet)
- **Input:** $3 per 1M tokens
- **Output:** $15 per 1M tokens

### Usage Estimates
| Scenario Type | Avg Tokens | Cost |
|---------------|-----------|------|
| Hiring Delay | ~800 | $0.06 |
| Employee Impact | ~900 | $0.07 |
| Component Risk | ~700 | $0.05 |
| Hiring Priority | ~1,200 | $0.09 |
| KT Success | ~1,000 | $0.08 |

**Monthly Budget (1000 scenarios):** ~$50-75

---

## 📚 Example Workflows

### Workflow 1: Hiring Decision Support
```
Manager: "Should we hire now or wait?"

1. Go to: Hiring Delay Impact Simulator
2. Enter: Component, 60-day delay, criticality level
3. AI predicts: Timeline delay, budget impact, risk increase
4. Result: Clear recommendation + alternatives
```

### Workflow 2: New Hire Evaluation
```
HR: "Is Jane a good hire for our team?"

1. Go to: Employee Impact Analyzer
2. Enter: Jane's role, components, salary, start date
3. AI predicts: Risk reductions, impact on critical components
4. Result: Recommendation + alternative scenarios
```

### Workflow 3: Annual Planning
```
Executive: "Where should we focus hiring this year?"

1. Go to: Hiring Priority Optimizer
2. Enter: Total budget, max number of hires
3. AI analyzes: All components, all risks, all opportunities
4. Result: Optimal sequenced hiring plan with ROI
```

---

## 🧠 How the AI Works

### Scenario Engine Architecture

```
┌─────────────────────────────────────────┐
│  1. User Input (Scenario + Constraints) │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  2. Build Context (Current State Data)  │
│     - Team roster                       │
│     - Component assignments             │
│     - Exit dates, KT status             │
│     - Budget constraints                │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  3. Craft Intelligent Prompt            │
│     - Business context                  │
│     - Decision scenario                 │
│     - Constraints & rules               │
│     - Output format (JSON)              │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  4. Call Claude API                     │
│     - Stream reasoning                  │
│     - Generate structured output        │
│     - Provide alternatives              │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  5. Parse & Display Results             │
│     - Metrics (timeline, budget, risk)  │
│     - Recommendation                    │
│     - Confidence score                  │
│     - Alternative approaches            │
└─────────────────────────────────────────┘
```

### Key Intelligence Points

1. **Context Awareness:** AI understands team size, criticality, constraints
2. **Risk Modeling:** Predicts cascading effects of decisions
3. **Business Logic:** Considers hiring timelines, ramp-up periods, KT duration
4. **Alternative Generation:** Always suggests Plan B and Plan C
5. **Confidence Scoring:** AI rates its own certainty (0-100%)

---

## 🔬 Experiment Log

### Phase 1: Foundation (This Sprint)
- ✅ Created scenario_engine.py with Claude integration
- ✅ Built Scenario_Analysis.py UI
- ✅ Implemented 5 core scenarios
- ⏳ Testing with real data
- ⏳ Validating accuracy of predictions

### Phase 2: Refinement (Next Sprint)
- [ ] Add more scenario templates
- [ ] Integrate with database for historical accuracy
- [ ] Add visualization for complex scenarios
- [ ] Build scenario comparison (side-by-side)
- [ ] Add scenario saving/loading

### Phase 3: Production (Q2)
- [ ] Fine-tune prompts based on feedback
- [ ] Add cost model validation
- [ ] Implement scenario analytics
- [ ] Build recommendation confidence calibration
- [ ] Merge to main branch with docs

---

## 🧪 Testing the AI

### Quick Test 1: Hiring Delay Impact
```
1. Go to Scenario Analysis
2. Select "Hiring Impact: Delay hiring"
3. Component: Any component
4. Delay: 30 days
5. Criticality: standard
6. Click "Simulate"
```

Expected: Should show reasonable timeline/budget impacts

### Quick Test 2: Employee Impact
```
1. Select "Employee Impact: Add new hire"
2. Name: "Test Employee"
3. Role: "Developer"
4. Level: "mid"
5. Components: Any 2 components
6. Cost: €5000/month
7. Click "Simulate"
```

Expected: Should show risk reduction and budget impact

### Quick Test 3: Risk Assessment
```
1. Select "Component Risk"
2. Component: Any component
3. Click "Analyze Risk"
```

Expected: Should provide risk score and recommendations

---

## 📊 Success Criteria

We'll consider this successful when:

- [ ] AI predictions match manager expectations
- [ ] API cost < €100/month for reasonable usage
- [ ] Response time < 10 seconds per scenario
- [ ] Users prefer AI recommendations > manual analysis
- [ ] Scenarios actually improve hiring decisions

---

## 🐛 Known Limitations

1. **Historical Context:** AI doesn't have access to past decisions/outcomes
2. **Real-time Data:** Uses snapshot at time of analysis
3. **Complexity:** Simplified model of workforce dynamics
4. **Confidence:** AI may be overly confident about uncertain predictions
5. **Edge Cases:** Unusual scenarios may produce unreliable results

---

## 🔮 Future Ideas

### V2 Features
- **Scenario Comparison:** Compare Option A vs Option B side-by-side
- **Scenario Saving:** Save/share scenarios with team
- **Historical Validation:** Compare AI predictions to actual outcomes
- **Batch Analysis:** Analyze multiple scenarios at once
- **Drill-Down:** Explain *why* AI made each prediction

### V3 Features
- **ML Model Integration:** Use historical data to train custom models
- **Monte Carlo Simulation:** Run 1000 scenarios with uncertainty ranges
- **Portfolio Optimization:** Optimize entire hiring portfolio simultaneously
- **Sensitivity Analysis:** "What happens if X becomes 50% worse?"
- **Slack Integration:** Ask AI scenarios via Slack

---

## 📝 Development Guide

### Adding a New Scenario

1. **Add method to `AurorAI` engine:**
```python
def my_new_scenario(self, param1, param2, ...):
    """Describe what this scenario does."""
    prompt = f"""
    [Build intelligent prompt]
    """
    return self._call_claude_scenario(prompt, "my_scenario")
```

2. **Add UI section to `Scenario_Analysis.py`:**
```python
elif scenario_type == "My New Scenario":
    # Collect user inputs
    # Call simulator method
    # Display results
```

3. **Test with real data**

### Improving Prompts

Prompts are in `AurorAI` methods. To improve:
1. Try different wording
2. Add/remove context
3. Change output format
4. Test with edge cases
5. Iterate based on results

---

## 📞 Support & Questions

For issues or suggestions:
1. Check if API key is configured correctly
2. Verify components/team data exists
3. Check API quota at console.anthropic.com
4. Review error message in Streamlit

---

## 🎓 References

- Claude Model Card: https://www-cdn.anthropic.com/de8ba9b01c9ab7cbabf5c33b80b090fdee56ec1ee6b38a973b515e87e91fee53/Model_Card_Claude_3.pdf
- Anthropic API Docs: https://docs.anthropic.com/
- Prompt Engineering Guide: https://docs.anthropic.com/claude/docs/how-to-use-system-prompts

---

**Last Updated:** April 1, 2026  
**Branch:** aura-ai-prototype  
**Author:** AURA Development Team

