import math

from logic.finance_service import (
    add_finance_columns,
    calculate_employee_cost,
    calculate_employee_fte,
)


def test_calculate_employee_cost_uses_employee_specific_hourly_model() -> None:
    budget_data = {
        "Intern": {"monthly_cost": 2000, "yearly_budget": 24000, "hourly_rate": 20, "weekly_hours": 35}
    }
    employee_settings = {"Max": {"hourly_rate": 50, "weekly_hours": 20}}

    monthly, yearly = calculate_employee_cost("Max", "Intern", budget_data, employee_settings)

    assert math.isclose(monthly, (20 * 50 * 52) / 12, rel_tol=1e-9)
    assert math.isclose(yearly, 20 * 50 * 52, rel_tol=1e-9)


def test_calculate_employee_cost_falls_back_to_budget_defaults() -> None:
    budget_data = {
        "Extern": {"monthly_cost": 8000, "yearly_budget": 96000, "hourly_rate": 0, "weekly_hours": 0}
    }

    monthly, yearly = calculate_employee_cost("Nina", "Extern", budget_data, {})

    assert monthly == 8000
    assert yearly == 96000


def test_calculate_employee_fte_uses_settings_for_named_employee() -> None:
    budget_data = {"Intern": {"weekly_hours": 35}}
    employee_settings = {"Ivy": {"weekly_hours": 17.5}}

    fte = calculate_employee_fte("Ivy", "Intern", budget_data, employee_settings)

    assert math.isclose(fte, 0.5, rel_tol=1e-9)


def test_calculate_employee_fte_for_intern_without_settings_uses_budget_hours() -> None:
    budget_data = {"Intern": {"weekly_hours": 21}}

    fte = calculate_employee_fte("Tom", "Intern", budget_data, {})

    assert math.isclose(fte, 0.6, rel_tol=1e-9)


def test_calculate_employee_fte_for_non_intern_defaults_to_one() -> None:
    fte = calculate_employee_fte("Lea", "Lead Cost Employee (LCE)", {}, {})
    assert fte == 1.0


def test_add_finance_columns_enriches_dataframe_with_expected_columns() -> None:
    team_data = [
        {"name": "A", "employee_type": "Intern"},
        {"name": "B", "employee_type": "Extern"},
    ]
    budget_data = {
        "Intern": {"monthly_cost": 2000, "yearly_budget": 24000, "hourly_rate": 25, "weekly_hours": 35},
        "Extern": {"monthly_cost": 9000, "yearly_budget": 108000, "hourly_rate": 0, "weekly_hours": 0},
    }
    employee_settings = {"A": {"hourly_rate": 30, "weekly_hours": 35}}

    df = add_finance_columns(team_data, budget_data, employee_settings)

    assert "Monatliche Kosten" in df.columns
    assert "Jährliche Kosten" in df.columns
    assert "FTE" in df.columns
    assert len(df) == 2
    assert df.loc[df["name"] == "A", "Monatliche Kosten"].iloc[0] > 0
