from datetime import date, datetime

from logic.allocation_service import (
    check_overallocation,
    get_next_allocation_id,
    validate_allocation_dates,
)


def test_validate_allocation_dates_allows_equal_or_later_end_date() -> None:
    start = date(2026, 1, 1)
    same = date(2026, 1, 1)
    later = date(2026, 2, 1)

    assert validate_allocation_dates(start, same) is True
    assert validate_allocation_dates(start, later) is True


def test_validate_allocation_dates_rejects_earlier_end_date() -> None:
    assert validate_allocation_dates(date(2026, 3, 1), date(2026, 2, 1)) is False


def test_get_next_allocation_id_returns_incremented_max_id() -> None:
    allocations = [{"id": 0}, {"id": 3}, {"id": 2}]
    assert get_next_allocation_id(allocations) == 4


def test_get_next_allocation_id_returns_zero_for_empty_allocations() -> None:
    assert get_next_allocation_id([]) == 0


def test_check_overallocation_detects_capacity_violation() -> None:
    allocations = [
        {
            "employee": "Alice",
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 3, 1),
            "percentage": 60,
        }
    ]

    is_over, month, total = check_overallocation(
        allocations=allocations,
        employee="Alice",
        start_month=date(2026, 2, 1),
        end_month=date(2026, 2, 1),
        allocation_percentage=50,
    )

    assert is_over is True
    assert month == "2026-02"
    assert total == 110


def test_check_overallocation_supports_datetime_ranges_and_no_conflict() -> None:
    allocations = [
        {
            "employee": "Bob",
            "start_date": datetime(2026, 1, 15, 10, 30),
            "end_date": datetime(2026, 2, 20, 18, 0),
            "percentage": 40,
        }
    ]

    is_over, month, total = check_overallocation(
        allocations=allocations,
        employee="Bob",
        start_month=date(2026, 3, 1),
        end_month=date(2026, 3, 1),
        allocation_percentage=70,
    )

    assert is_over is False
    assert month is None
    assert total == 70
