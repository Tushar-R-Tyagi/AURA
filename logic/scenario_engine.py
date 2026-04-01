"""
🌟 AURORA - AI-powered scenario simulation engine for workforce planning.
Uses Groq's Mixtral/Llama models to predict impact of management decisions.

AURORA helps workforce managers answer critical what-if questions:
- What if we delay hiring for this component?
- What if we add a new team member?
- Where should we prioritize new hires?
- What's our knowledge transfer risk?
- How will our budget be affected?
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import TypedDict

from groq import Groq


class ScenarioResult(TypedDict):
    """Structure for scenario analysis results."""
    scenario_type: str
    timeline_impact_days: int
    budget_impact_euros: float
    risk_increase_percent: float
    recommendation: str
    reasoning: str
    alternatives: list[dict]
    confidence_score: float  # 0-100%


class AurorAI:
    """
    AURORA: AI-powered scenario simulator using Claude's decision reasoning.
    
    Analyzes workforce management what-if scenarios to predict:
    - Timeline impacts
    - Budget consequences
    - Risk changes
    - Recommended alternatives
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Groq API client."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not set. "
                "Set via environment variable or pass to __init__"
            )
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Groq's available fast model
    
    def simulate_hiring_delay(
        self,
        component_name: str,
        delay_days: int,
        current_staffing: int,
        required_staffing: int,
        component_criticality: str,  # "critical", "important", "standard"
        budget_remaining_euros: float,
        team_data: list[dict],
        components_data: list[dict],
    ) -> ScenarioResult:
        """
        Simulate impact of delaying hiring for a component.
        
        Args:
            component_name: Name of component
            delay_days: How many days to delay hiring start
            current_staffing: Current number of people
            required_staffing: Required number for component
            component_criticality: How critical is this component
            budget_remaining_euros: Budget available
            team_data: Current team roster
            components_data: Component definitions
        
        Returns:
            ScenarioResult with predicted impacts and recommendations
        """
        
        context = self._build_hiring_context(
            component_name,
            current_staffing,
            required_staffing,
            component_criticality,
            team_data,
            components_data,
        )
        
        prompt = f"""
You are an expert workforce planning consultant. Analyze this scenario:

{context}

SCENARIO: We delay hiring for {component_name} by {delay_days} days.
This means the hiring process starts {delay_days} days later than originally planned.

Based on industry standards and best practices, provide your analysis in JSON format:

{{
  "timeline_impact_days": <estimated project delay in days>,
  "budget_impact_euros": <additional costs (negative = savings)>,
  "risk_increase_percent": <increase in failure risk 0-100>,
  "recommendation": "<brief recommendation: EXECUTE, RECONSIDER, or AVOID>",
  "reasoning": "<2-3 sentences explaining your analysis>",
  "alternatives": [
    {{
      "option": "<alternative approach>",
      "timeline_impact": <days>,
      "budget_impact": <euros>,
      "pros": "<benefits>",
      "cons": "<drawbacks>"
    }},
    ...
  ],
  "confidence_score": <0-100>
}}

Be specific with numbers. Consider:
- Current staffing gaps
- Component criticality
- Budget constraints
- Industry standard hiring timelines (60-90 days)
- Knowledge transfer requirements
"""
        
        return self._call_claude_scenario(prompt, "hiring_delay")
    
    def simulate_employee_addition(
        self,
        employee_name: str,
        employee_role: str,
        employee_level: str,  # "junior", "mid", "senior"
        components_assigned: list[str],
        start_date: str,
        budget_impact_monthly_euros: float,
        team_data: list[dict],
        components_data: list[dict],
    ) -> ScenarioResult:
        """
        Simulate impact of adding a new employee.
        
        Args:
            employee_name: Name of new hire
            employee_role: Role/position
            employee_level: Experience level
            components_assigned: Components this person will work on
            start_date: When they start
            budget_impact_monthly_euros: Monthly salary cost
            team_data: Current team
            components_data: Component definitions
        
        Returns:
            ScenarioResult with predicted impacts
        """
        
        context = self._build_employee_context(
            employee_name,
            employee_role,
            employee_level,
            components_assigned,
            team_data,
            components_data,
        )
        
        prompt = f"""
You are an expert workforce planning consultant. Analyze this hiring decision:

{context}

NEW EMPLOYEE:
- Name: {employee_name}
- Role: {employee_role}
- Level: {employee_level}
- Start date: {start_date}
- Monthly cost: €{budget_impact_monthly_euros:,.0f}
- Assigned to: {', '.join(components_assigned)}

Provide your analysis in JSON format:

{{
  "timeline_impact_days": <timeline improvement in days (negative = delays)>,
  "budget_impact_euros": <total cost including salary, training, ramp-up>,
  "risk_decrease_percent": <reduction in failure risk 0-100>,
  "recommendation": "<HIRE, CONDITIONAL, or HOLD>",
  "reasoning": "<2-3 sentences on ROI and impact>",
  "knock_on_effects": [
    "<unexpected consequences or benefits>"
  ],
  "alternatives": [
    {{
      "option": "<alternative approach>",
      "pros": "<benefits>",
      "cons": "<drawbacks>",
      "cost": <euros>
    }}
  ],
  "confidence_score": <0-100>
}}

Consider:
- Component dependencies
- Ramp-up time for level
- Knowledge transfer burden on team
- Total cost of employment (salary + training + ramp-up)
- Impact on other team members
"""
        
        return self._call_claude_scenario(prompt, "employee_addition")
    
    def analyze_component_risk(
        self,
        component_name: str,
        current_staffing: int,
        required_staffing: int,
        responsible_persons: list[str],
        knowledge_transfer_status: str,
        components_data: list[dict],
        team_data: list[dict],
    ) -> dict:
        """
        Analyze risk for a specific component.
        
        Returns risk assessment with recommendations.
        """
        
        context = self._build_risk_context(
            component_name,
            current_staffing,
            required_staffing,
            responsible_persons,
            knowledge_transfer_status,
            components_data,
            team_data,
        )
        
        prompt = f"""
You are an expert risk analyst. Assess the risk for this component:

{context}

Provide JSON analysis:

{{
  "risk_score": <0-100, where 100 is complete failure>,
  "risk_level": "<CRITICAL, HIGH, MEDIUM, LOW>",
  "single_point_of_failure": <true/false>,
  "months_until_critical": <estimated months before crisis>,
  "immediate_actions": [
    "<action required NOW>"
  ],
  "priority_hiring": [
    {{
      "role": "<role to hire>",
      "urgency": "<IMMEDIATE, 30 days, 60 days>",
      "reason": "<why this role>"
    }}
  ],
  "alternatives_to_hiring": [
    {{
      "approach": "<alternative>",
      "cost": <euros>,
      "effectiveness": <0-100%>
    }}
  ]
}}

Be specific. Consider:
- Current vs required staffing
- Knowledge transfer status
- Exit dates in next 24 months
- Component criticality
- Industry benchmarks
"""
        
        return self._call_claude_scenario(prompt, "risk_analysis")
    
    def recommend_hiring_priority(
        self,
        available_budget_euros: float,
        max_hires: int,
        components_data: list[dict],
        team_data: list[dict],
    ) -> dict:
        """
        Use AI to recommend optimal hiring priority given constraints.
        
        Answers: "We can hire 2 people with €180K. Which components first?"
        """
        
        context = self._build_hiring_priority_context(
            components_data,
            team_data,
        )
        
        prompt = f"""
You are an expert workforce optimizer. I have constraints:
- Budget available: €{available_budget_euros:,.0f}
- Maximum hires allowed: {max_hires}

Current portfolio:

{context}

Recommend the optimal hiring sequence to:
1. Minimize overall risk
2. Protect critical path components
3. Maximize ROI
4. Stay within budget

Provide JSON response:

{{
  "recommended_sequence": [
    {{
      "priority": 1,
      "component": "<component name>",
      "hire_count": <number of people>,
      "role": "<specific role>",
      "level": "<junior/mid/senior>",
      "cost": <monthly salary>,
      "rationale": "<why hire this first>",
      "risk_reduction": <0-100%>,
      "timeline_impact": "<improves by X months or avoids Y month delay>"
    }},
    ...
  ],
  "total_cost": <euros>,
  "why_this_sequence": "<key reasoning>",
  "risks_if_not_followed": [
    "<risk if not followed>"
  ],
  "confidence_score": <0-100>
}}

Be strategic. This is the company's hiring roadmap.
"""
        
        return self._call_claude_scenario(prompt, "hiring_priority")
    
    def predict_kt_success(
        self,
        component_name: str,
        departing_person: dict,
        replacement_person: dict = None,
        planned_kt_weeks: int = 8,
        team_data: list[dict] = None,
        components_data: list[dict] = None,
    ) -> dict:
        """
        Predict success probability of knowledge transfer scenario.
        """
        
        replacement_info = (
            f"Replacement: {replacement_person['name']} "
            f"({replacement_person.get('role', 'Unknown')})"
            if replacement_person
            else "Replacement: Not yet assigned"
        )
        
        prompt = f"""
You are an expert in knowledge transfer assessment.

SCENARIO:
- Component: {component_name}
- Departing: {departing_person['name']} ({departing_person.get('role', 'Unknown')})
- {replacement_info}
- Planned KT duration: {planned_kt_weeks} weeks

Predict knowledge transfer success in JSON:

{{
  "success_probability": <0-100%>,
  "risk_level": "<CRITICAL, HIGH, MEDIUM, LOW>",
  "loss_assessment": "<what will definitely be lost>",
  "kt_plan": [
    {{
      "phase": "<phase name>",
      "weeks": <duration>,
      "activities": ["<activity>", ...],
      "critical_tasks": ["<must cover>", ...],
      "success_metrics": ["<how to measure>", ...]
    }},
    ...
  ],
  "budget_for_kt": <euros for training, external help, etc>,
  "contingency_plan": "<if KT fails, then...>",
  "confidence_score": <0-100>
}}

Be realistic about what can be transferred in {planned_kt_weeks} weeks.
"""
        
        return self._call_claude_scenario(prompt, "kt_prediction")
    
    def ask_custom_question(
        self,
        question: str,
        team_data: list[dict] = None,
        components_data: list[dict] = None,
        budget_data: dict = None,
        analysis_type: str = "standard",
    ) -> dict:
        """
        Free-form custom question mode.
        
        Allows users to ask any workforce-related question without predefined scenarios.
        AURORA reasons through company context and provides structured analysis.
        
        Args:
            question: User's question (e.g., "Can we deliver Q3 roadmap with 20% fewer developers?")
            team_data: Current team roster
            components_data: Project/component definitions
            budget_data: Budget information
            analysis_type: "standard" (direct answer), "sensitivity" (explore ranges), 
                          "comparative" (compare options), "hypothesis" (validate theory)
        
        Returns:
            Dictionary with answer, reasoning, confidence, and recommendations
        """
        
        # Build company context
        context = self._build_custom_context(team_data, components_data, budget_data)
        
        # Different prompts based on analysis type
        if analysis_type == "comparative":
            prompt = self._build_comparative_prompt(question, context)
        elif analysis_type == "sensitivity":
            prompt = self._build_sensitivity_prompt(question, context)
        elif analysis_type == "hypothesis":
            prompt = self._build_hypothesis_prompt(question, context)
        else:  # standard
            prompt = self._build_standard_prompt(question, context)
        
        return self._call_custom_question_api(prompt, analysis_type)
    
    def _build_standard_prompt(self, question: str, context: str) -> str:
        """Build standard open-ended reasoning prompt."""
        return f"""
You are an expert workforce planning consultant and strategic advisor.

COMPANY CONTEXT:
{context}

USER QUESTION: {question}

Provide a comprehensive analysis in JSON format:

{{
  "answer": "<direct, concise answer to the question>",
  "key_factors_considered": [
    "<factor 1>",
    "<factor 2>",
    ...
  ],
  "analysis": "<2-3 paragraph detailed reasoning>",
  "recommendations": [
    {{
      "action": "<recommended action>",
      "rationale": "<why>",
      "expected_impact": "<what will happen>",
      "risk": "<what could go wrong>",
      "timeline": "<how long will it take>"
    }},
    ...
  ],
  "alternative_perspectives": [
    {{
      "perspective": "<alternative viewpoint>",
      "why_relevant": "<why consider this>",
      "pros": "<advantages>",
      "cons": "<disadvantages>"
    }},
    ...
  ],
  "confidence_score": <0-100>,
  "confidence_explanation": "<why this confidence level>"
}}

Be specific with numbers and timelines. Consider industry best practices and realistic constraints.
"""
    
    def _build_comparative_prompt(self, question: str, context: str) -> str:
        """Build prompt for comparing multiple options."""
        return f"""
You are an expert workforce planning consultant.

COMPANY CONTEXT:
{context}

USER QUESTION: {question}

The user is asking to compare different options or approaches. 
Provide structured JSON comparing alternatives:

{{
  "question_analysis": "<breakdown of what's being compared>",
  "options_compared": [
    {{
      "option_name": "<name of option>",
      "description": "<what is this option>",
      "pros": ["<pro 1>", "<pro 2>", ...],
      "cons": ["<con 1>", "<con 2>", ...],
      "timeline_impact": "<effect on timelines>",
      "budget_impact": "<cost or savings>",
      "risk_level": "<LOW, MEDIUM, HIGH>",
      "implementation_difficulty": "<EASY, MODERATE, DIFFICULT>"
    }},
    ...
  ],
  "recommended_option": {{
    "choice": "<which option is best>",
    "rationale": "<why this one>",
    "conditions": ["<condition 1>", "<condition 2>", ...]
  }},
  "hybrid_approach": "<if combining options could work>",
  "confidence_score": <0-100>
}}

Be analytical and data-driven in comparisons.
"""
    
    def _build_sensitivity_prompt(self, question: str, context: str) -> str:
        """Build prompt for sensitivity/what-if analysis."""
        return f"""
You are an expert workforce planning consultant.

COMPANY CONTEXT:
{context}

USER QUESTION: {question}

The user is interested in understanding how outcomes change with different assumptions.
Provide JSON with sensitivity analysis:

{{
  "base_case": {{
    "scenario": "<baseline scenario>",
    "outcome": "<what happens if nothing changes>"
  }},
  "sensitivity_dimensions": [
    {{
      "variable": "<what's being changed>",
      "best_case": {{
        "value": "<optimistic value>",
        "outcome": "<best case outcome>",
        "confidence": <0-100>
      }},
      "base_case": {{
        "value": "<realistic/expected value>",
        "outcome": "<baseline outcome>",
        "confidence": <0-100>
      }},
      "worst_case": {{
        "value": "<pessimistic value>",
        "outcome": "<worst case outcome>",
        "confidence": <0-100>
      }}
    }},
    ...
  ],
  "breakeven_analysis": "<what assumptions would change the recommendation>",
  "most_sensitive_to": "<which variable matters most>",
  "recommendations": "<which scenario is most likely and recommended>",
  "confidence_score": <0-100>
}}

Identify the critical variables that matter most to the decision.
"""
    
    def _build_hypothesis_prompt(self, question: str, context: str) -> str:
        """Build prompt for validating user hypotheses/theories."""
        return f"""
You are an expert workforce planning consultant.

COMPANY CONTEXT:
{context}

USER HYPOTHESIS/THEORY: {question}

The user has a theory or hypothesis about workforce planning. 
Validate or challenge it with objective analysis:

{{
  "hypothesis": "<the user's theory restated>",
  "assessment": "<LIKELY TRUE / UNCERTAIN / PROBABLY FALSE>",
  "supporting_evidence": [
    "<evidence or reasoning that supports the hypothesis>",
    ...
  ],
  "contradicting_evidence": [
    "<evidence or reasoning that contradicts the hypothesis>",
    ...
  ],
  "conditions_for_truth": [
    "<condition that must be met for hypothesis to be true>",
    ...
  ],
  "detailed_analysis": "<3-4 paragraph objective analysis>",
  "recommendation": "{{
    "action": "<what to do based on analysis>",
    "rationale": "<why>",
    "monitoring_metrics": ["<metric to track>", ...]
  }}",
  "confidence_score": <0-100>,
  "needed_validation": ["<what data would confirm this>", ...]
}}

Be balanced and consider both sides. Give honest assessment even if contradicts user's theory.
"""
    
    def _build_custom_context(
        self,
        team_data: list[dict],
        components_data: list[dict],
        budget_data: dict,
    ) -> str:
        """Build general company context for custom questions."""
        
        # Team summary
        team_summary = f"Current team: {len(team_data or [])} people" if team_data else "Team data: Not available"
        
        # Components summary
        if components_data:
            comp_summary = f"{len(components_data)} components/projects"
            comp_names = [c.get("component_name", "Unknown") for c in components_data[:5]]
            comp_summary += f": {', '.join(comp_names)}"
        else:
            comp_summary = "No component data available"
        
        # Budget summary
        if budget_data:
            total_budget = budget_data.get("total_budget_euros", 0)
            spent = budget_data.get("spent_euros", 0)
            remaining = total_budget - spent
            budget_summary = (
                f"Budget: €{total_budget:,.0f} total, "
                f"€{spent:,.0f} spent, "
                f"€{remaining:,.0f} remaining"
            )
        else:
            budget_summary = "Budget data: Not available"
        
        return f"""
ORGANIZATION:
- {team_summary}
- {comp_summary}
- {budget_summary}

Please consider this context when answering the user's question.
"""
    
    def _call_custom_question_api(self, prompt: str, analysis_type: str) -> dict:
        """Call Groq API for custom questions."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=3000,  # Allow more tokens for detailed analysis
                messages=[{"role": "user", "content": prompt}],
            )
            
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            result["analysis_type"] = analysis_type
            result["full_response"] = response_text  # Store original for transparency
            
            return result
        
        except Exception as e:
            return {
                "error": f"API Error: {str(e)}",
                "analysis_type": analysis_type,
                "confidence_score": 0,
            }
    
    # ===== HELPER METHODS =====
    
    def _build_hiring_context(
        self,
        component_name: str,
        current_staffing: int,
        required_staffing: int,
        component_criticality: str,
        team_data: list[dict],
        components_data: list[dict],
    ) -> str:
        """Build context about hiring delay scenario."""
        
        component_info = next(
            (c for c in components_data if c.get("component_name") == component_name),
            {},
        )
        
        # Find exits in next 12 months
        exits_soon = [
            e for e in team_data
            if e.get("days_until_exit", 999) < 365
        ]
        
        return f"""
COMPONENT INFORMATION:
- Name: {component_name}
- Criticality: {component_criticality}
- Current staffing: {current_staffing}
- Required staffing: {required_staffing} (gap: {required_staffing - current_staffing})
- Responsible persons: {', '.join(component_info.get('responsible_persons', []))}
- Knowledge transfer time: {component_info.get('knowledge_transfer_time_needed', 6)} months

TEAM CONTEXT:
- Total team size: {len(team_data)}
- Exits planned in next 12 months: {len(exits_soon)}
- Team capacity: {(current_staffing / required_staffing * 100):.0f}% of target

BUSINESS CONTEXT:
- Industry: Siemens internal
- Average hiring time: 60-90 days
- Component strategic importance: {component_criticality}
"""
    
    def _build_employee_context(
        self,
        employee_name: str,
        employee_role: str,
        employee_level: str,
        components_assigned: list[str],
        team_data: list[dict],
        components_data: list[dict],
    ) -> str:
        """Build context about new employee."""
        
        component_gaps = []
        for comp in components_assigned:
            comp_data = next(
                (c for c in components_data if c.get("component_name") == comp),
                {},
            )
            required = comp_data.get("required_resources", 1)
            current = len([
                t for t in team_data
                if comp in (t.get("components") or "").split(",")
            ])
            gap = required - current
            if gap > 0:
                component_gaps.append(f"- {comp}: {gap} people needed")
        
        return f"""
NEW HIRE PROFILE:
- Name: {employee_name}
- Role: {employee_role}
- Level: {employee_level}
- Components assigned: {', '.join(components_assigned)}

COMPONENT GAPS BEING FILLED:
{chr(10).join(component_gaps) if component_gaps else "- No gaps, optimizing capacity"}

TEAM STRUCTURE:
- Current size: {len(team_data)}
- Ramp-up overhead: {employee_level in ['junior', 'mid'] and '15-20%' or '5%'} of team capacity
"""
    
    def _build_risk_context(
        self,
        component_name: str,
        current_staffing: int,
        required_staffing: int,
        responsible_persons: list[str],
        knowledge_transfer_status: str,
        components_data: list[dict],
        team_data: list[dict],
    ) -> str:
        """Build risk assessment context."""
        
        component_info = next(
            (c for c in components_data if c.get("component_name") == component_name),
            {},
        )
        
        # Check exits for responsible persons
        responsible_exits = []
        for person in responsible_persons:
            person_data = next(
                (t for t in team_data if t.get("name") == person),
                {},
            )
            if person_data:
                days_left = person_data.get("days_until_exit", 999)
                responsible_exits.append(
                    f"- {person}: {days_left} days until exit"
                )
        
        return f"""
COMPONENT: {component_name}
- Complexity score: {component_info.get('complexity_score', 5)}/10
- Required staffing: {required_staffing}
- Current staffing: {current_staffing}
- Staffing gap: {required_staffing - current_staffing}
- Knowledge transfer status: {knowledge_transfer_status}
- Documentation status: {component_info.get('documentation_status', 'Unknown')}
- Backup available: {component_info.get('backup_available', False)}

RESPONSIBLE PERSONS:
{chr(10).join(responsible_exits) if responsible_exits else "- No immediate exits"}

CRITICALITY INDICATORS:
- Single point of failure: {current_staffing == 1}
- Skills difficult to find: {component_info.get('complexity_score', 5) > 7}
"""
    
    def _build_hiring_priority_context(
        self,
        components_data: list[dict],
        team_data: list[dict],
    ) -> str:
        """Build context for hiring priority recommendations."""
        
        priority_list = []
        for comp in components_data:
            comp_name = comp.get("component_name")
            required = comp.get("required_resources", 1)
            responsible = comp.get("responsible_persons", [])
            
            priority_list.append(
                f"- {comp_name}: {required} required, "
                f"Responsible: {', '.join(responsible) if responsible else 'Unassigned'}"
            )
        
        return "\n".join(priority_list)
    
    def _call_claude_scenario(self, prompt: str, scenario_type: str) -> dict:
        """Call Groq API and parse scenario response."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ValueError("No JSON found in Groq response")
            
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            result["scenario_type"] = scenario_type
            result["reasoning"] = response_text[:json_start].strip()
            
            return result
        
        except Exception as e:
            return {
                "error": f"API Error: {str(e)}",
                "scenario_type": scenario_type,
                "confidence_score": 0,
            }
