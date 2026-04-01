"""
Visualization service for AURORA scenario simulations.
Creates interactive Plotly charts to display simulation results.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta


def create_timeline_impact_chart(timeline_impact_days: int, component_name: str) -> go.Figure:
    """Create chart showing timeline impact in days."""
    
    fig = go.Figure()
    
    # Current vs impacted timeline
    scenarios = ["Original Timeline", "With Delay"]
    days = [0, timeline_impact_days]
    colors = ["#00B8A9", "#F8B195"]
    
    fig.add_trace(go.Bar(
        x=scenarios,
        y=days,
        marker=dict(color=colors),
        text=[f"{d} days" for d in days],
        textposition="auto",
        hovertemplate="<b>%{x}</b><br>Delay: %{y} days<extra></extra>"
    ))
    
    fig.update_layout(
        title=f"📅 Timeline Impact for {component_name}",
        yaxis_title="Days of Delay",
        xaxis_title="Scenario",
        height=300,
        showlegend=False,
        hovermode="closest"
    )
    
    return fig


def create_budget_impact_chart(budget_impact: float, component_name: str) -> go.Figure:
    """Create gauge chart for budget impact."""
    
    # Determine color based on impact
    if budget_impact > 0:
        delta_color = "red"
        impact_label = f"+€{budget_impact:,.0f} (additional cost)"
    else:
        delta_color = "green"
        impact_label = f"€{budget_impact:,.0f} (savings)"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=abs(budget_impact),
        title={"text": f"💰 Budget Impact ({component_name})"},
        domain={"x": [0, 1], "y": [0, 1]},
        delta={"reference": 0, "suffix": "€"},
        gauge={
            "axis": {"range": [None, abs(budget_impact) * 1.2]},
            "bar": {"color": delta_color},
            "steps": [
                {"range": [0, abs(budget_impact) * 0.3], "color": "lightgray"},
                {"range": [abs(budget_impact) * 0.3, abs(budget_impact) * 0.7], "color": "gray"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": abs(budget_impact) * 0.9
            }
        }
    ))
    
    fig.update_layout(height=350)
    return fig


def create_risk_gauge_chart(risk_increase: float, component_name: str) -> go.Figure:
    """Create gauge chart for risk level."""
    
    # Determine color based on risk
    if risk_increase < 20:
        color = "green"
        risk_level = "LOW"
    elif risk_increase < 50:
        color = "yellow"
        risk_level = "MEDIUM"
    elif risk_increase < 80:
        color = "orange"
        risk_level = "HIGH"
    else:
        color = "red"
        risk_level = "CRITICAL"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_increase,
        title={"text": f"⚠️ Risk Increase ({component_name})"},
        domain={"x": [0, 1], "y": [0, 1]},
        suffix="%",
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 25], "color": "#90EE90"},
                {"range": [25, 50], "color": "#FFD700"},
                {"range": [50, 75], "color": "#FFA500"},
                {"range": [75, 100], "color": "#FF6B6B"}
            ],
            "threshold": {
                "line": {"color": "darkred", "width": 4},
                "thickness": 0.75,
                "value": 90
            }
        },
        number={"suffix": f"% → {risk_level}"}
    ))
    
    fig.update_layout(height=350)
    return fig


def create_confidence_gauge_chart(confidence_score: float) -> go.Figure:
    """Create gauge chart for AI confidence score."""
    
    if confidence_score >= 80:
        color = "green"
        level = "HIGH"
    elif confidence_score >= 60:
        color = "yellow"
        level = "MEDIUM"
    else:
        color = "orange"
        level = "LOW"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence_score,
        title={"text": "🤖 AI Confidence"},
        domain={"x": [0, 1], "y": [0, 1]},
        suffix="%",
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 40], "color": "#FFE0E0"},
                {"range": [40, 70], "color": "#FFF8DC"},
                {"range": [70, 100], "color": "#E0FFE0"}
            ]
        },
        number={"suffix": f"% ({level})"}
    ))
    
    fig.update_layout(height=300)
    return fig


def create_hiring_priority_chart(recommendations: list[dict]) -> go.Figure:
    """Create bar chart showing hiring priorities."""
    
    if not recommendations:
        return create_empty_chart("No recommendations available")
    
    df = pd.DataFrame([
        {
            "Component": rec.get("component", "Unknown"),
            "Priority": rec.get("priority", 0),
            "Cost": rec.get("cost", 0),
            "Risk Reduction": rec.get("risk_reduction", 0)
        }
        for rec in recommendations[:5]  # Top 5
    ])
    
    fig = px.bar(
        df,
        x="Component",
        y="Priority",
        color="Risk Reduction",
        title="📊 Hiring Priority Ranking",
        labels={"Priority": "Priority Order", "Component": "Component"},
        color_continuous_scale="RdYlGn"
    )
    
    fig.update_layout(
        height=350,
        hovermode="closest",
        xaxis_tickangle=-45
    )
    
    return fig


def create_hiring_impact_timeline(timeline_breakpoints: list[dict], component_name: str) -> go.Figure:
    """Create timeline chart showing project phases and hiring impact."""
    
    if not timeline_breakpoints:
        return create_empty_chart("No timeline data available")
    
    df = pd.DataFrame([
        {
            "Phase": bp.get("phase", "Unknown"),
            "Days": bp.get("days", 0),
            "Impact": bp.get("impact", "None")
        }
        for bp in timeline_breakpoints
    ])
    
    fig = go.Figure(data=[
        go.Bar(
            x=df["Phase"],
            y=df["Days"],
            name="Duration",
            marker_color="#00B8A9"
        )
    ])
    
    fig.update_layout(
        title=f"📅 Project Timeline Impact for {component_name}",
        xaxis_title="Project Phase",
        yaxis_title="Days",
        height=350,
        hovermode="closest"
    )
    
    return fig


def create_alternatives_comparison(alternatives: list[dict]) -> go.Figure:
    """Create comparison chart of alternative approaches."""
    
    if not alternatives:
        return create_empty_chart("No alternatives available")
    
    # Prepare data
    df = pd.DataFrame([
        {
            "Option": alt.get("option", f"Alternative {i+1}"),
            "Timeline Impact (days)": alt.get("timeline_impact", 0),
            "Budget (€)": alt.get("budget_impact", 0),
            "Effectiveness (%)": alt.get("effectiveness", 0)
        }
        for i, alt in enumerate(alternatives[:5])
    ])
    
    # Normalize for comparison
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="Timeline Impact",
        x=df["Option"],
        y=df["Timeline Impact (days)"],
        marker_color="lightblue"
    ))
    
    fig.add_trace(go.Bar(
        name="Effectiveness (%)",
        x=df["Option"],
        y=df["Effectiveness (%)"],
        marker_color="lightgreen"
    ))
    
    fig.update_layout(
        title="💡 Alternative Approaches Comparison",
        xaxis_title="Option",
        height=350,
        barmode="group",
        hovermode="closest",
        xaxis_tickangle=-45
    )
    
    return fig


def create_risk_heatmap(components_risk_data: list[dict]) -> go.Figure:
    """Create heatmap showing risk across components."""
    
    if not components_risk_data:
        return create_empty_chart("No risk data available")
    
    df = pd.DataFrame(components_risk_data)
    
    if len(df) == 0:
        return create_empty_chart("No components to display")
    
    # Create heatmap
    risk_matrix = df.pivot_table(
        index="component_name",
        values="risk_score",
        aggfunc="first"
    ).fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=risk_matrix.values,
        x=["Risk Score"],
        y=risk_matrix.index,
        colorscale="RdYlGn_r",
        colorbar=dict(title="Risk %")
    ))
    
    fig.update_layout(
        title="🔥 Risk Heatmap Across Components",
        height=max(300, len(risk_matrix) * 40),
        hovermode="closest"
    )
    
    return fig


def create_knowledge_transfer_timeline(kt_plan: list[dict]) -> go.Figure:
    """Create timeline chart for knowledge transfer phases."""
    
    if not kt_plan:
        return create_empty_chart("No KT plan available")
    
    df = pd.DataFrame([
        {
            "Phase": phase.get("phase", "Unknown"),
            "Weeks": phase.get("weeks", 0),
            "Completion": phase.get("weeks", 0)  # For cumulative
        }
        for phase in kt_plan
    ])
    
    # Calculate cumulative weeks
    df["Cumulative"] = df["Weeks"].cumsum()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df["Phase"],
        y=df["Weeks"],
        name="Duration",
        marker_color="#FF6B6B",
        text=df["Weeks"],
        textposition="auto"
    ))
    
    fig.add_trace(go.Scatter(
        x=df["Phase"],
        y=df["Cumulative"],
        name="Cumulative",
        mode="lines+markers",
        marker=dict(size=10, color="#00B8A9"),
        line=dict(color="#00B8A9", width=2)
    ))
    
    fig.update_layout(
        title="📚 Knowledge Transfer Timeline",
        xaxis_title="KT Phase",
        yaxis_title="Weeks",
        height=350,
        hovermode="closest",
        yaxis2=dict(
            title="Cumulative Weeks",
            overlaying="y",
            side="right"
        )
    )
    
    return fig


def create_budget_vs_impact_scatter(scenarios: list[dict]) -> go.Figure:
    """Create scatter plot of budget vs timeline impact."""
    
    if not scenarios:
        return create_empty_chart("No scenario data")
    
    df = pd.DataFrame([
        {
            "Scenario": s.get("name", f"Scenario {i+1}"),
            "Budget Impact (€)": s.get("budget_impact", 0),
            "Timeline Impact (days)": s.get("timeline_impact", 0),
            "Risk": s.get("risk_increase", 0)
        }
        for i, s in enumerate(scenarios)
    ])
    
    fig = px.scatter(
        df,
        x="Budget Impact (€)",
        y="Timeline Impact (days)",
        size="Risk",
        color="Risk",
        hover_name="Scenario",
        title="💰 Budget vs Timeline Trade-off",
        color_continuous_scale="Reds"
    )
    
    fig.update_layout(
        height=350,
        hovermode="closest"
    )
    
    return fig


def create_empty_chart(message: str = "No data available") -> go.Figure:
    """Create a placeholder chart with a message."""
    
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        height=300
    )
    
    return fig
