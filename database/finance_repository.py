"""Repository helpers for finance-related persistence."""

from __future__ import annotations

from database.connection import get_connection


def load_budget_data() -> dict:
    """Load all persisted budget defaults by employee type."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT employee_type, monthly_cost, yearly_budget, hourly_rate, weekly_hours FROM budget_settings"
        ).fetchall()

    return {
        row["employee_type"]: {
            "monthly_cost": row["monthly_cost"],
            "yearly_budget": row["yearly_budget"],
            "hourly_rate": row["hourly_rate"],
            "weekly_hours": row["weekly_hours"],
        }
        for row in rows
    }


def save_budget_data(budget_data: dict) -> None:
    """Persist the current budget defaults."""
    with get_connection() as connection:
        connection.execute("DELETE FROM budget_settings")
        for employee_type, values in budget_data.items():
            connection.execute(
                """
                INSERT INTO budget_settings (
                    employee_type, monthly_cost, yearly_budget, hourly_rate, weekly_hours
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    employee_type,
                    float(values.get("monthly_cost", 0)),
                    float(values.get("yearly_budget", 0)),
                    float(values.get("hourly_rate", 0)),
                    float(values.get("weekly_hours", 0)),
                ),
            )
        connection.commit()


def load_employee_settings() -> dict:
    """Load persisted per-employee custom hour settings."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT employee_name, hourly_rate, weekly_hours FROM employee_settings"
        ).fetchall()

    return {
        row["employee_name"]: {
            "hourly_rate": row["hourly_rate"],
            "weekly_hours": int(row["weekly_hours"]),
        }
        for row in rows
    }


def save_employee_settings(employee_settings: dict) -> None:
    """Persist all employee-specific finance settings."""
    with get_connection() as connection:
        connection.execute("DELETE FROM employee_settings")
        for employee_name, values in employee_settings.items():
            connection.execute(
                "INSERT INTO employee_settings (employee_name, hourly_rate, weekly_hours) VALUES (?, ?, ?)",
                (
                    employee_name,
                    float(values.get("hourly_rate", 0)),
                    float(values.get("weekly_hours", 0)),
                ),
            )
        connection.commit()
