"""Project allocation business rules extracted from the Streamlit page."""

from __future__ import annotations

from datetime import date, datetime


def _normalize_to_date(value: date | datetime) -> date:
    """Normalize date-like values for reliable comparisons."""
    if isinstance(value, datetime):
        return value.date()
    return value


def _next_month(current: date) -> date:
    """Return the first day of the next month."""
    if current.month == 12:
        return current.replace(year=current.year + 1, month=1)
    return current.replace(month=current.month + 1)


def validate_allocation_dates(start_month: date, end_month: date) -> bool:
    """Ensure the allocation period is valid."""
    return end_month >= start_month


def get_next_allocation_id(allocations: list[dict]) -> int:
    """Return the next safe allocation ID for persisted storage."""
    existing_ids = [int(allocation.get("id", -1)) for allocation in allocations]
    return max(existing_ids, default=-1) + 1


def check_overallocation(
    allocations: list[dict],
    employee: str,
    start_month: date,
    end_month: date,
    allocation_percentage: int,
) -> tuple[bool, str | None, int]:
    """Check whether a new allocation would push an employee above 100%."""
    check_date = start_month.replace(day=1)
    normalized_end = end_month.replace(day=1)

    while check_date <= normalized_end:
        total_allocation = allocation_percentage
        for alloc in allocations:
            alloc_start = _normalize_to_date(alloc["start_date"])
            alloc_end = _normalize_to_date(alloc["end_date"])
            if alloc["employee"] == employee and alloc_start <= check_date <= alloc_end:
                total_allocation += int(alloc["percentage"])

        if total_allocation > 100:
            return True, check_date.strftime("%Y-%m"), total_allocation

        check_date = _next_month(check_date)

    return False, None, allocation_percentage
