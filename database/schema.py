"""Schema and bootstrap logic for the SQLite database."""

from __future__ import annotations

import json

from database.connection import get_connection
from database.defaults import (
    DEFAULT_BUDGET_DATA,
    DEFAULT_TEAM_DATA,
    PERSISTED_STATE_DEFAULTS,
)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_order INTEGER NOT NULL DEFAULT 0,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    employee_type TEXT NOT NULL,
    components TEXT,
    start_date TEXT,
    planned_exit TEXT,
    knowledge_transfer_status TEXT,
    priority TEXT,
    dob TEXT,
    team TEXT,
    manual_override INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS budget_settings (
    employee_type TEXT PRIMARY KEY,
    monthly_cost REAL NOT NULL DEFAULT 0,
    yearly_budget REAL NOT NULL DEFAULT 0,
    hourly_rate REAL NOT NULL DEFAULT 0,
    weekly_hours REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS employee_settings (
    employee_name TEXT PRIMARY KEY,
    hourly_rate REAL NOT NULL DEFAULT 0,
    weekly_hours REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_allocations (
    id INTEGER PRIMARY KEY,
    employee TEXT NOT NULL,
    project TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    percentage INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL
);
"""


TEAM_INSERT_SQL = """
INSERT INTO team_members (
    display_order,
    name,
    role,
    employee_type,
    components,
    start_date,
    planned_exit,
    knowledge_transfer_status,
    priority,
    dob,
    team,
    manual_override
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def initialize_database() -> None:
    """Create tables and seed defaults the first time the app runs."""
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)

        team_count = connection.execute("SELECT COUNT(*) FROM team_members").fetchone()[0]
        if team_count == 0:
            for index, member in enumerate(DEFAULT_TEAM_DATA):
                connection.execute(
                    TEAM_INSERT_SQL,
                    (
                        index,
                        member["name"],
                        member["role"],
                        member["employee_type"],
                        member.get("components", ""),
                        member.get("start_date"),
                        member.get("planned_exit"),
                        member.get("knowledge_transfer_status"),
                        member.get("priority"),
                        member.get("dob"),
                        member.get("team", "Unassigned"),
                        int(member.get("manual_override", False)),
                    ),
                )

        budget_count = connection.execute("SELECT COUNT(*) FROM budget_settings").fetchone()[0]
        if budget_count == 0:
            for employee_type, values in DEFAULT_BUDGET_DATA.items():
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

        for key, default_value in PERSISTED_STATE_DEFAULTS.items():
            connection.execute(
                "INSERT OR IGNORE INTO app_config (key, value_json) VALUES (?, ?)",
                (key, json.dumps(default_value)),
            )

        connection.commit()
