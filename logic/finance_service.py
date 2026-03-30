"""Finance-related business logic extracted from the Streamlit page."""

from __future__ import annotations

import pandas as pd


def calculate_employee_cost(
    emp_name: str,
    emp_type: str,
    budget_data: dict,
    employee_settings: dict,
) -> tuple[float, float]:
    """Calculate monthly and yearly costs for an employee."""
    if emp_type == "Intern" and emp_name in employee_settings:
        settings = employee_settings[emp_name]
        hourly_rate = settings.get("hourly_rate", budget_data[emp_type]["hourly_rate"])
        weekly_hours = settings.get("weekly_hours", budget_data[emp_type]["weekly_hours"])
        monthly = (weekly_hours * hourly_rate * 52) / 12
        yearly = weekly_hours * hourly_rate * 52
    else:
        monthly = budget_data.get(emp_type, {}).get("monthly_cost", 0)
        yearly = budget_data.get(emp_type, {}).get("yearly_budget", 0)
    return monthly, yearly


def calculate_employee_fte(
    emp_name: str,
    emp_type: str,
    budget_data: dict,
    employee_settings: dict,
) -> float:
    """Calculate FTE (full-time equivalent) for an employee."""
    if emp_type == "Intern":
        if emp_name in employee_settings:
            weekly_hours = employee_settings[emp_name].get(
                "weekly_hours", budget_data[emp_type]["weekly_hours"]
            )
        else:
            weekly_hours = budget_data[emp_type]["weekly_hours"]
        return weekly_hours / 35 if weekly_hours > 0 else 0.0
    return 1.0


def add_finance_columns(team_data: list[dict], budget_data: dict, employee_settings: dict) -> pd.DataFrame:
    """Return a dataframe enriched with finance and FTE columns."""
    df = pd.DataFrame(team_data)
    if df.empty:
        return df

    df["Monatliche Kosten"] = df.apply(
        lambda row: calculate_employee_cost(
            row["name"], row["employee_type"], budget_data, employee_settings
        )[0],
        axis=1,
    )
    df["Jährliche Kosten"] = df.apply(
        lambda row: calculate_employee_cost(
            row["name"], row["employee_type"], budget_data, employee_settings
        )[1],
        axis=1,
    )
    df["FTE"] = df.apply(
        lambda row: calculate_employee_fte(
            row["name"], row["employee_type"], budget_data, employee_settings
        ),
        axis=1,
    )
    return df
