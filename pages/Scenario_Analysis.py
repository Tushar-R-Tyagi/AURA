import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from database.session_store import ensure_session_state
from logic.scenario_engine import AurorAI
from logic.team_service import build_team_dataframe
from logic.visualization_service import (
    create_timeline_impact_chart,
    create_budget_impact_chart,
    create_risk_gauge_chart,
    create_confidence_gauge_chart,
    create_alternatives_comparison,
)
from ui.theme import load_theme, render_sidebar_navigation

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


st.set_page_config(
    page_title="🤖 AURORA",
    page_icon="🤖",
    layout="wide"
)

ensure_session_state()
load_theme()
render_sidebar_navigation()

st.title("🤖 AURORA - Scenario Simulator")
st.markdown("Use AI to predict impact of your workforce decisions")
st.markdown("---")

# Initialize session state
st.session_state.setdefault("scenario_results", None)

# Check for API key
api_key = st.session_state.get("groq_api_key")
if not api_key:
    api_key = None  # Will use environment variable

# Try to initialize simulator
try:
    aurora = AurorAI(api_key=api_key)
    api_ready = True
except ValueError as e:
    api_ready = False
    api_error = str(e)

if not api_ready:
    st.error(f"⚠️ AI Service Error: {api_error}")
    st.info(
        """
        To use scenario simulations, you need a FREE Groq API key:
        1. Set environment variable: `GROQ_API_KEY=gsk_...`
        2. Or enter your API key in the sidebar below
        
        Get your **FREE** API key at: https://console.groq.com/
        
        """
    )
    
    with st.expander("💡 Enter API Key Manually"):
        input_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Your key will only be used for this session"
        )
        if input_key:
            st.session_state.groq_api_key = input_key
            st.info("✅ API key set for this session. Refresh the page to use it.")

if api_ready:
    # Main scenario selection
    scenario_type = st.selectbox(
        "📊 What scenario do you want to explore?",
        [
            "--- Select a scenario ---",
            "Hiring Impact: Delay hiring for a component",
            "Employee Impact: Add a new hire",
            "Component Risk: Assess risk for a component",
            "Hiring Priority: Where should we hire first?",
            "Knowledge Transfer: Will KT succeed?",
        ]
    )

    st.markdown("---")

    # ===== SCENARIO 1: HIRING DELAY =====
    if scenario_type == "Hiring Impact: Delay hiring for a component":
        st.markdown("### 📅 Hiring Delay Impact Simulator")
        st.markdown(
            "Predict what happens if you delay hiring for a critical component"
        )

        df_team = build_team_dataframe(st.session_state.team_data)
        components_list = [
            c.get("component_name")
            for c in st.session_state.get("components_data", [])
            if c.get("component_name")
        ]

        col1, col2 = st.columns(2)

        with col1:
            selected_component = st.selectbox(
                "Component to delay hiring for",
                components_list or ["No components found"]
            )

            delay_days = st.slider(
                "Hiring delay (days)",
                min_value=0,
                max_value=180,
                value=30,
                step=15,
                help="How many days to push back hiring start date"
            )

        with col2:
            criticality = st.select_slider(
                "Component criticality",
                options=["low", "standard", "important", "critical"],
                value="standard"
            )

            budget_remaining = st.number_input(
                "Budget remaining (€)",
                min_value=0,
                value=100000,
                step=5000
            )

        if st.button("🔮 Simulate Impact", type="primary", use_container_width=True):
            if selected_component == "No components found":
                st.error("Please add components first in Stammdaten Management")
            else:
                with st.spinner("🤔 AURORA analyzing scenario..."):
                    # Get component details
                    comp_data = next(
                        (c for c in st.session_state.components_data
                         if c.get("component_name") == selected_component),
                        {}
                    )

                    result = aurora.simulate_hiring_delay(
                        component_name=selected_component,
                        delay_days=delay_days,
                        current_staffing=len([
                            t for t in st.session_state.team_data
                            if selected_component in (t.get("components") or "").split(",")
                        ]),
                        required_staffing=comp_data.get("required_resources", 1),
                        component_criticality=criticality,
                        budget_remaining_euros=budget_remaining,
                        team_data=st.session_state.team_data,
                        components_data=st.session_state.get("components_data", []),
                    )

                    st.session_state.scenario_results = result
                    st.rerun()

        # Display results
        if st.session_state.scenario_results:
            results = st.session_state.scenario_results

            if "error" not in results:
                st.success("✅ Analysis Complete")

                # Display reasoning
                if results.get("reasoning"):
                    with st.expander("💭 AURORA Reasoning"):
                        st.write(results["reasoning"])

                # Impact metrics
                st.markdown("### 📈 Predicted Impact")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    timeline_impact = results.get("timeline_impact_days", 0)
                    st.metric(
                        "Timeline Delay",
                        f"+{timeline_impact} days",
                        delta=f"+{timeline_impact}" if timeline_impact > 0 else "No delay",
                        delta_color="inverse"
                    )

                with col2:
                    budget_impact = results.get("budget_impact_euros", 0)
                    st.metric(
                        "Budget Impact",
                        f"€{budget_impact:,.0f}",
                        delta=f"€+{budget_impact:,.0f}" if budget_impact > 0 else "No cost",
                        delta_color="inverse"
                    )

                with col3:
                    risk_increase = results.get("risk_increase_percent", 0)
                    st.metric(
                        "Risk Increase",
                        f"+{risk_increase:.0f}%",
                        delta=f"+{risk_increase:.0f}%",
                        delta_color="inverse"
                    )

                with col4:
                    confidence = results.get("confidence_score", 0)
                    st.metric(
                        "AURORA Confidence",
                        f"{confidence:.0f}%",
                        help="How confident is AURORA in this prediction?"
                    )

                # Prognose visualizations
                st.markdown("### 📊 Prognose & Visualisierungen")
                
                viz_col1, viz_col2 = st.columns(2)
                
                with viz_col1:
                    timeline_chart = create_timeline_impact_chart(
                        timeline_impact, 
                        selected_component
                    )
                    st.plotly_chart(timeline_chart, use_container_width=True)
                
                with viz_col2:
                    budget_chart = create_budget_impact_chart(
                        budget_impact,
                        selected_component
                    )
                    st.plotly_chart(budget_chart, use_container_width=True)
                
                viz_col3, viz_col4 = st.columns(2)
                
                with viz_col3:
                    risk_chart = create_risk_gauge_chart(
                        risk_increase,
                        selected_component
                    )
                    st.plotly_chart(risk_chart, use_container_width=True)
                
                with viz_col4:
                    conf_chart = create_confidence_gauge_chart(confidence)
                    st.plotly_chart(conf_chart, use_container_width=True)

                # Recommendation
                st.markdown("### 🎯 AURORA Recommendation")
                recommendation = results.get("recommendation", "No recommendation")

                if "AVOID" in recommendation:
                    st.error(f"❌ {recommendation}")
                elif "RECONSIDER" in recommendation:
                    st.warning(f"⚠️ {recommendation}")
                else:
                    st.info(f"✅ {recommendation}")

                # Alternatives
                if results.get("alternatives"):
                    st.markdown("### 💡 Alternative Approaches")
                    
                    # Show comparison chart
                    alt_chart = create_alternatives_comparison(results["alternatives"])
                    st.plotly_chart(alt_chart, use_container_width=True)

                    for i, alt in enumerate(results["alternatives"], 1):
                        with st.expander(f"Option {i}: {alt.get('option', 'Alternative')}"):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric(
                                    "Timeline Impact",
                                    f"{alt.get('timeline_impact', 0)} days"
                                )

                            with col2:
                                st.metric(
                                    "Budget Cost",
                                    f"€{alt.get('budget_impact', 0):,.0f}"
                                )

                            with col3:
                                st.metric(
                                    "Effectiveness",
                                    f"{alt.get('effectiveness', 0)}%"
                                )

                            if alt.get("pros"):
                                st.write(f"**Pros:** {alt['pros']}")
                            if alt.get("cons"):
                                st.write(f"**Cons:** {alt['cons']}")

            else:
                st.error(f"❌ Error: {results.get('error')}")
                st.info("Please check your API key and try again")

    # ===== SCENARIO 2: EMPLOYEE IMPACT =====
    elif scenario_type == "Employee Impact: Add a new hire":
        st.markdown("### 👤 New Employee Impact Simulator")
        st.markdown(
            "Predict the impact of adding a new employee to your team"
        )

        col1, col2 = st.columns(2)

        with col1:
            emp_name = st.text_input("New employee name", value="New Hire")
            emp_role = st.text_input("Role/Position", value="Developer")

        with col2:
            emp_level = st.select_slider(
                "Experience level",
                options=["junior", "mid", "senior"],
                value="mid"
            )
            start_date = st.date_input("Start date", value=datetime.now())

        components_list = [
            c.get("component_name")
            for c in st.session_state.get("components_data", [])
            if c.get("component_name")
        ]

        components_assigned = st.multiselect(
            "Assign to components",
            components_list or ["No components"],
            help="Which components will this person work on?"
        )

        col1, col2 = st.columns(2)

        with col1:
            monthly_cost = st.number_input(
                "Monthly salary (€)",
                min_value=1000,
                value=5000,
                step=500
            )

        with col2:
            job_impact = st.text_input(
                "Expected impact (optional)",
                value="Will fill staffing gap",
                help="Brief description of why we're hiring this role"
            )

        if st.button("🔮 Simulate Impact", type="primary", use_container_width=True):
            if not components_assigned or components_assigned[0] == "No components":
                st.error("Please assign the employee to at least one component")
            else:
                with st.spinner("🤔 AURORA analyzing impact..."):
                    result = aurora.simulate_employee_addition(
                        employee_name=emp_name,
                        employee_role=emp_role,
                        employee_level=emp_level,
                        components_assigned=components_assigned,
                        start_date=start_date.isoformat(),
                        budget_impact_monthly_euros=monthly_cost,
                        team_data=st.session_state.team_data,
                        components_data=st.session_state.get("components_data", []),
                    )

                    st.session_state.scenario_results = result
                    st.rerun()

        if st.session_state.scenario_results:
            results = st.session_state.scenario_results

            if "error" not in results:
                st.success("✅ Analysis Complete")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    timeline_impact = results.get("timeline_impact_days", 0)
                    st.metric(
                        "Timeline Impact",
                        f"{timeline_impact:+.0f} days",
                        help="Positive = improves timeline"
                    )

                with col2:
                    budget_impact = results.get("budget_impact_euros", 0)
                    st.metric("Total Cost", f"€{budget_impact:,.0f}")

                with col3:
                    risk_decrease = results.get("risk_decrease_percent", 0)
                    st.metric(
                        "Risk Reduction",
                        f"-{risk_decrease:.0f}%",
                        help="Lower is better"
                    )

                with col4:
                    confidence = results.get("confidence_score", 0)
                    st.metric("AURORA Confidence", f"{confidence:.0f}%")

                # Recommendation
                st.markdown("### 🎯 AURORA Recommendation")
                recommendation = results.get("recommendation", "No recommendation")

                if "HIRE" in recommendation:
                    st.success(f"✅ {recommendation}")
                elif "CONDITIONAL" in recommendation:
                    st.warning(f"🟡 {recommendation}")
                else:
                    st.info(f"ℹ️ {recommendation}")

                # Knockon effects
                if results.get("knock_on_effects"):
                    st.markdown("### ⚡ Knock-On Effects")
                    for effect in results["knock_on_effects"]:
                        st.write(f"• {effect}")

                # Alternatives
                if results.get("alternatives"):
                    st.markdown("### 💡 Alternative Approaches")

                    for i, alt in enumerate(results["alternatives"], 1):
                        with st.expander(f"Option {i}: {alt.get('option', 'Alternative')}"):
                            st.write(f"**Pros:** {alt.get('pros', 'N/A')}")
                            st.write(f"**Cons:** {alt.get('cons', 'N/A')}")
                            st.write(f"**Cost:** €{alt.get('cost', 0):,.0f}")

            else:
                st.error(f"❌ Error: {results.get('error')}")

    # ===== SCENARIO 3: COMPONENT RISK =====
    elif scenario_type == "Component Risk: Assess risk for a component":
        st.markdown("### 🚨 Component Risk Assessment")
        st.markdown("Analyze current risk level for a component")

        components_list = [
            c.get("component_name")
            for c in st.session_state.get("components_data", [])
            if c.get("component_name")
        ]

        selected_component = st.selectbox(
            "Select component to analyze",
            components_list or ["No components found"]
        )

        if st.button("🔍 Analyze Risk", type="primary", use_container_width=True):
            if selected_component == "No components found":
                st.error("Please add components first")
            else:
                with st.spinner("🤔 AURORA analyzing risk..."):
                    comp_data = next(
                        (c for c in st.session_state.components_data
                         if c.get("component_name") == selected_component),
                        {}
                    )

                    result = aurora.analyze_component_risk(
                        component_name=selected_component,
                        current_staffing=len([
                            t for t in st.session_state.team_data
                            if selected_component in (t.get("components") or "").split(",")
                        ]),
                        required_staffing=comp_data.get("required_resources", 1),
                        responsible_persons=comp_data.get("responsible_persons", []),
                        knowledge_transfer_status=comp_data.get(
                            "knowledge_transfer_status", "Unknown"
                        ),
                        components_data=st.session_state.get("components_data", []),
                        team_data=st.session_state.team_data,
                    )

                    st.session_state.scenario_results = result
                    st.rerun()

        if st.session_state.scenario_results:
            results = st.session_state.scenario_results

            if "error" not in results:
                # Risk level indicator
                risk_score = results.get("risk_score", 50)
                risk_level = results.get("risk_level", "MEDIUM")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if risk_score < 30:
                        st.success(f"✅ Risk Level: {risk_level} ({risk_score}/100)")
                    elif risk_score < 60:
                        st.warning(f"🟡 Risk Level: {risk_level} ({risk_score}/100)")
                    else:
                        st.error(f"🔴 Risk Level: {risk_level} ({risk_score}/100)")

                with col2:
                    single_pof = results.get("single_point_of_failure", False)
                    if single_pof:
                        st.error("⚠️ Single Point of Failure!")
                    else:
                        st.success("✅ Multiple resources available")

                with col3:
                    months_critical = results.get("months_until_critical", 999)
                    if months_critical < 3:
                        st.error(f"🔴 Critical in {months_critical} months")
                    elif months_critical < 12:
                        st.warning(f"🟡 Critical in {months_critical} months")
                    else:
                        st.success(f"✅ Stable for {months_critical} months")

                # Immediate actions
                if results.get("immediate_actions"):
                    st.markdown("### ⚡ Immediate Actions Required")
                    for action in results["immediate_actions"]:
                        st.error(f"🚨 {action}")

                # Priority hiring
                if results.get("priority_hiring"):
                    st.markdown("### 👥 Priority Hiring Needed")
                    for hire in results["priority_hiring"]:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Role:** {hire.get('role')}")
                        with col2:
                            st.write(f"**Urgency:** {hire.get('urgency')}")
                        with col3:
                            st.write(f"**Reason:** {hire.get('reason')}")

                # Alternatives to hiring
                if results.get("alternatives_to_hiring"):
                    st.markdown("### 💡 Alternatives to Hiring")
                    for alt in results["alternatives_to_hiring"]:
                        st.write(
                            f"**{alt.get('approach')}** - Cost: €{alt.get('cost', 0):,.0f}, "
                            f"Effectiveness: {alt.get('effectiveness', 0)}%"
                        )

            else:
                st.error(f"❌ Error: {results.get('error')}")

    # ===== SCENARIO 4: HIRING PRIORITY =====
    elif scenario_type == "Hiring Priority: Where should we hire first?":
        st.markdown("### 🎯 Hiring Priority Optimization")
        st.markdown(
            "AI-powered recommendation for optimal hiring sequence given your constraints"
        )

        col1, col2 = st.columns(2)

        with col1:
            available_budget = st.number_input(
                "Available hiring budget (€)",
                min_value=50000,
                value=200000,
                step=10000
            )

        with col2:
            max_hires = st.number_input(
                "Maximum hires allowed",
                min_value=1,
                value=3,
                step=1
            )

        st.info(
            f"💡 Finding optimal way to hire {max_hires} people with €{available_budget:,} "
            "to minimize risk and maximize ROI"
        )

        if st.button("🔮 Get Recommendations", type="primary", use_container_width=True):
            with st.spinner("🤔 AI optimizing hiring sequence..."):
                result = aurora.recommend_hiring_priority(
                    available_budget_euros=available_budget,
                    max_hires=max_hires,
                    components_data=st.session_state.get("components_data", []),
                    team_data=st.session_state.team_data,
                )

                st.session_state.scenario_results = result
                st.rerun()

        if st.session_state.scenario_results:
            results = st.session_state.scenario_results

            if "error" not in results:
                st.success("✅ Optimization Complete")

                st.markdown("### 📋 Recommended Hiring Sequence")
                st.write(f"**Key Reasoning:** {results.get('why_this_sequence', 'N/A')}")
                st.metric("Total Cost", f"€{results.get('total_cost', 0):,.0f}")

                for i, hire in enumerate(results.get("recommended_sequence", []), 1):
                    with st.expander(
                        f"Priority {i}: {hire.get('component')} - {hire.get('role')}",
                        expanded=(i == 1)
                    ):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Hire Count",
                                hire.get("hire_count"),
                                help="Number of people to hire"
                            )
                            st.metric(
                                "Level",
                                hire.get("level").capitalize()
                            )

                        with col2:
                            st.metric(
                                "Monthly Cost",
                                f"€{hire.get('cost', 0):,.0f}",
                                help="Per person salary"
                            )
                            st.metric(
                                "Risk Reduction",
                                f"{hire.get('risk_reduction', 0)}%"
                            )

                        with col3:
                            st.metric(
                                "Timeline Impact",
                                hire.get("timeline_impact", "TBD")
                            )

                        st.write(f"**Rationale:** {hire.get('rationale', 'N/A')}")

                # Risks if not followed
                if results.get("risks_if_not_followed"):
                    st.markdown("### ⚠️ Risks If Not Followed")
                    for risk in results["risks_if_not_followed"]:
                        st.warning(f"• {risk}")

            else:
                st.error(f"❌ Error: {results.get('error')}")

    # ===== SCENARIO 5: KNOWLEDGE TRANSFER =====
    elif scenario_type == "Knowledge Transfer: Will KT succeed?":
        st.markdown("### 📚 Knowledge Transfer Success Prediction")
        st.markdown("Predict success probability of knowledge transfer before someone leaves")

        df_team = build_team_dataframe(st.session_state.team_data)

        if df_team.empty:
            st.error("No team members found")
        else:
            # Get people leaving soon
            departing = df_team[df_team["days_until_exit"] < 365].sort_values(
                "days_until_exit"
            )

            if departing.empty:
                st.info("No team members with planned exits found")
            else:
                departing_person = st.selectbox(
                    "Person leaving",
                    departing["name"].tolist(),
                    help="Select the person whose knowledge needs to be transferred"
                )

                departing_data = departing[departing["name"] == departing_person].iloc[0]

                col1, col2 = st.columns(2)

                with col1:
                    kt_weeks = st.slider(
                        "Knowledge transfer duration (weeks)",
                        min_value=2,
                        max_value=24,
                        value=8
                    )

                with col2:
                    replacement_assigned = st.checkbox(
                        "Replacement employee already assigned?"
                    )

                if replacement_assigned:
                    remaining_team = [
                        t for t in df_team["name"]
                        if t != departing_person
                    ]
                    replacement_person = st.selectbox(
                        "Replacement person",
                        remaining_team
                    )
                else:
                    replacement_person = None

                st.info(
                    f"Days until {departing_person} leaves: "
                    f"{int(departing_data['days_until_exit'])} days"
                )

                if st.button("🔮 Analyze KT Success", type="primary", use_container_width=True):
                    with st.spinner("🤔 AURORA analyzing KT scenario..."):
                        departing_dict = {
                            "name": departing_person,
                            "role": departing_data["role"],
                        }

                        replacement_dict = None
                        if replacement_person:
                            replacement_data = df_team[
                                df_team["name"] == replacement_person
                            ].iloc[0]
                            replacement_dict = {
                                "name": replacement_person,
                                "role": replacement_data["role"],
                            }

                        result = aurora.predict_kt_success(
                            component_name=departing_data.get("components", "Unknown"),
                            departing_person=departing_dict,
                            replacement_person=replacement_dict,
                            planned_kt_weeks=kt_weeks,
                            team_data=st.session_state.team_data,
                            components_data=st.session_state.get("components_data", []),
                        )

                        st.session_state.scenario_results = result
                        st.rerun()

                if st.session_state.scenario_results:
                    results = st.session_state.scenario_results

                    if "error" not in results:
                        success_prob = results.get("success_probability", 50)

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if success_prob > 80:
                                st.success(f"✅ Success Probability: {success_prob}%")
                            elif success_prob > 60:
                                st.warning(f"🟡 Success Probability: {success_prob}%")
                            else:
                                st.error(f"🔴 Success Probability: {success_prob}%")

                        with col2:
                            risk_level = results.get("risk_level", "UNKNOWN")
                            st.write(f"**Risk Level:** {risk_level}")

                        with col3:
                            budget_for_kt = results.get("budget_for_kt", 0)
                            st.metric("Recommended KT Budget", f"€{budget_for_kt:,.0f}")

                        # Loss assessment
                        st.markdown("### 📊 Loss Assessment")
                        st.write(results.get("loss_assessment", "N/A"))

                        # KT Plan phases
                        if results.get("kt_plan"):
                            st.markdown("### 📋 Recommended KT Plan")

                            for phase in results["kt_plan"]:
                                with st.expander(
                                    f"{phase.get('phase')} ({phase.get('weeks')} weeks)",
                                    expanded=True
                                ):
                                    st.write("**Activities:**")
                                    for activity in phase.get("activities", []):
                                        st.write(f"• {activity}")

                                    if phase.get("critical_tasks"):
                                        st.write("**Critical Tasks:**")
                                        for task in phase["critical_tasks"]:
                                            st.write(f"✓ {task}")

                                    if phase.get("success_metrics"):
                                        st.write("**Success Metrics:**")
                                        for metric in phase["success_metrics"]:
                                            st.write(f"📊 {metric}")

                        # Contingency
                        st.markdown("### 🆘 If KT Fails")
                        contingency = results.get("contingency_plan", "No contingency available")
                        st.error(contingency)

                    else:
                        st.error(f"❌ Error: {results.get('error')}")

else:
    st.info("⚠️ Waiting for API configuration...")
