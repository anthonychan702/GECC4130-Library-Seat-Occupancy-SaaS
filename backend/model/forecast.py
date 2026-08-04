from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time
from statistics import mean
from typing import Iterable, Protocol
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")


class OccupancyRow(Protocol):
    hour_str: str
    occupant_count: int


@dataclass(frozen=True)
class ForecastPoint:
    time: str
    occupancy: int
    is_forecast: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "time": self.time,
            "occupancy": self.occupancy,
            "is_forecast": self.is_forecast,
        }


def library_open_hours(weekday: int) -> list[int]:
    """weekday follows date.weekday(): Monday=0 ... Sunday=6."""
    if weekday <= 4:
        return list(range(8, 22))
    if weekday == 5:
        return list(range(8, 19))
    return list(range(11, 19))


def parse_hour_str(hour_str: str) -> datetime | None:
    try:
        return datetime.strptime(hour_str, "%Y-%m-%d_%H").replace(tzinfo=HKT)
    except (TypeError, ValueError):
        return None


def _recent_same_weekday_values(
    rows: Iterable[OccupancyRow],
    target: date,
    lookback_weeks: int,
) -> tuple[dict[int, list[int]], dict[int, list[int]]]:
    same_weekday: dict[int, list[int]] = defaultdict(list)
    all_history: dict[int, list[int]] = defaultdict(list)
    earliest = target.fromordinal(target.toordinal() - lookback_weeks * 7)

    for row in rows:
        timestamp = parse_hour_str(row.hour_str)
        if timestamp is None:
            continue
        row_date = timestamp.date()
        if not earliest <= row_date < target:
            continue

        occupancy = max(0, int(row.occupant_count or 0))
        all_history[timestamp.hour].append(occupancy)
        if row_date.weekday() == target.weekday():
            same_weekday[timestamp.hour].append(occupancy)

    return same_weekday, all_history


def _robust_average(values: list[int]) -> float | None:
    if not values:
        return None
    if len(values) < 5:
        return mean(values)

    ordered = sorted(values)
    trim_count = max(1, int(len(ordered) * 0.1))
    trimmed = ordered[trim_count:-trim_count]
    return mean(trimmed or ordered)


def forecast_today_series(
    historical_rows: Iterable[OccupancyRow],
    *,
    target_date: date | None = None,
    lookback_weeks: int = 8,
    max_capacity: int = 500,
) -> list[dict[str, object]]:
    """
    Return hourly occupancy forecasts for the target date.

    Baseline model: for each open hour, average the same weekday across the
    most recent lookback_weeks. If no same-weekday observation exists, fall
    back to all available historical observations for that hour, then zero.
    """
    if lookback_weeks < 1:
        raise ValueError("lookback_weeks must be at least 1")
    if max_capacity < 1:
        raise ValueError("max_capacity must be at least 1")

    target = target_date or datetime.now(HKT).date()
    same_weekday, all_history = _recent_same_weekday_values(
        historical_rows,
        target,
        lookback_weeks,
    )

    result: list[dict[str, object]] = []
    for hour in library_open_hours(target.weekday()):
        prediction = _robust_average(same_weekday.get(hour, []))
        if prediction is None:
            prediction = _robust_average(all_history.get(hour, []))
        predicted_occupancy = min(max_capacity, max(0, round(prediction or 0)))
        result.append(
            ForecastPoint(
                time=f"{hour:02d}:00",
                occupancy=predicted_occupancy,
            ).as_dict()
        )

    return result


def forecast_today_response(
    historical_rows: Iterable[OccupancyRow],
    *,
    target_date: date | None = None,
    lookback_weeks: int = 8,
    max_capacity: int = 500,
) -> dict[str, object]:
    target = target_date or datetime.now(HKT).date()
    return {
        "date": target.isoformat(),
        "timezone": "Asia/Hong_Kong",
        "model": "same_weekday_hourly_baseline",
        "series": forecast_today_series(
            historical_rows,
            target_date=target,
            lookback_weeks=lookback_weeks,
            max_capacity=max_capacity,
        ),
    }