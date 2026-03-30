"""Repository helpers for project allocation persistence."""

from __future__ import annotations

from datetime import date, datetime

from database.connection import get_connection


def _to_storage_date(value: str | date | datetime) -> str:
    """Normalize date-like values for SQLite storage."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _from_storage_date(value: str) -> date:
    """Parse an ISO date from the database."""
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_project_allocations() -> list[dict]:
    """Load all persisted project allocations."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, employee, project, start_date, end_date, percentage FROM project_allocations ORDER BY id"
        ).fetchall()

    return [
        {
            "id": row["id"],
            "employee": row["employee"],
            "project": row["project"],
            "start_date": _from_storage_date(row["start_date"]),
            "end_date": _from_storage_date(row["end_date"]),
            "percentage": int(row["percentage"]),
        }
        for row in rows
    ]


def save_project_allocations(project_allocations: list[dict]) -> None:
    """Persist the full set of project allocations."""
    with get_connection() as connection:
        connection.execute("DELETE FROM project_allocations")
        for fallback_id, allocation in enumerate(project_allocations):
            connection.execute(
                """
                INSERT INTO project_allocations (id, employee, project, start_date, end_date, percentage)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(allocation.get("id", fallback_id)),
                    allocation["employee"],
                    allocation["project"],
                    _to_storage_date(allocation["start_date"]),
                    _to_storage_date(allocation["end_date"]),
                    int(allocation.get("percentage", 0)),
                ),
            )
        connection.commit()
