"""Repository helpers for employee/team persistence."""

from __future__ import annotations

from database.connection import get_connection


def load_team_members() -> list[dict]:
    """Load all persisted team members in UI display order."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
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
            FROM team_members
            ORDER BY display_order, id
            """
        ).fetchall()

    return [
        {
            "name": row["name"],
            "role": row["role"],
            "employee_type": row["employee_type"],
            "components": row["components"] or "",
            "start_date": row["start_date"],
            "planned_exit": row["planned_exit"],
            "knowledge_transfer_status": row["knowledge_transfer_status"],
            "priority": row["priority"],
            "dob": row["dob"],
            "team": row["team"] or "Unassigned",
            "manual_override": bool(row["manual_override"]),
        }
        for row in rows
    ]


def save_team_members(team_data: list[dict]) -> None:
    """Replace persisted team data with the latest in-memory state."""
    with get_connection() as connection:
        connection.execute("DELETE FROM team_members")
        for index, member in enumerate(team_data):
            connection.execute(
                """
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
                """,
                (
                    index,
                    member["name"],
                    member["role"],
                    member.get("employee_type", "Intern"),
                    member.get("components", ""),
                    member.get("start_date"),
                    member.get("planned_exit"),
                    member.get("knowledge_transfer_status", "Not Started"),
                    member.get("priority", "Low"),
                    member.get("dob"),
                    member.get("team", "Unassigned"),
                    int(member.get("manual_override", False)),
                ),
            )
        connection.commit()
