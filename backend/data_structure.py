from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, List, Optional, Set


def _normalize_pref(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if s.upper() in {"N/A", "NA", "NONE", "NULL", "ANY", "ALL"}:
        return None
    if s in {"不限", "全部", "任何"}:
        return None
    return s


def _safe_rate(occupied: int, capacity: Optional[int]) -> Optional[float]:
    if capacity is None or capacity <= 0:
        return None
    return max(0.0, min(1.0, occupied / capacity))


@dataclass(slots=True)
class Snapshot:
    observed_at: datetime
    occupied_count: int
    available_count: Optional[int]
    occupancy_rate: Optional[float]
    source_type: str = "manual"
    confidence_score: Optional[float] = None


@dataclass(slots=True)
class ForecastPoint:
    forecast_for: datetime
    predicted_occupied_count: Optional[float]
    predicted_occupancy_rate: Optional[float]
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


@dataclass(slots=True)
class ZoneMeta:
    zone_id: int
    zone_name: str
    floor_label: str
    zone_type: str
    capacity: Optional[int] = None
    library_id: Optional[int] = None
    is_active: bool = True


@dataclass(slots=True)
class Recommendation:
    zone_id: int
    zone_name: str
    floor_label: str
    zone_type: str
    score: float
    current_rate: Optional[float]
    forecast_rate: Optional[float]
    occupied_count: Optional[int]
    available_count: Optional[int]
    reason: str


@dataclass
class ZoneState:
    meta: ZoneMeta
    current: Optional[Snapshot] = None
    recent: Deque[Snapshot] = field(default_factory=lambda: deque(maxlen=288))
    forecast: List[ForecastPoint] = field(default_factory=list)

    def current_rate(self) -> Optional[float]:
        if self.current and self.current.occupancy_rate is not None:
            return self.current.occupancy_rate
        if self.current:
            return _safe_rate(self.current.occupied_count, self.meta.capacity)
        return None

    def forecast_rate(self) -> Optional[float]:
        if not self.forecast:
            return None

        rates: List[float] = []
        for p in self.forecast[:3]:
            if p.predicted_occupancy_rate is not None:
                rates.append(p.predicted_occupancy_rate)
            elif p.predicted_occupied_count is not None and self.meta.capacity:
                rates.append(
                    max(0.0, min(1.0, p.predicted_occupied_count / self.meta.capacity))
                )

        if not rates:
            return None
        return sum(rates) / len(rates)

    def to_dict(self) -> dict:
        return {
            "zone_id": self.meta.zone_id,
            "zone_name": self.meta.zone_name,
            "floor_label": self.meta.floor_label,
            "zone_type": self.meta.zone_type,
            "capacity": self.meta.capacity,
            "is_active": self.meta.is_active,
            "current": None
            if not self.current
            else {
                "observed_at": self.current.observed_at.isoformat(),
                "occupied_count": self.current.occupied_count,
                "available_count": self.current.available_count,
                "occupancy_rate": self.current.occupancy_rate,
                "source_type": self.current.source_type,
                "confidence_score": self.current.confidence_score,
            },
            "forecast": [
                {
                    "forecast_for": p.forecast_for.isoformat(),
                    "predicted_occupied_count": p.predicted_occupied_count,
                    "predicted_occupancy_rate": p.predicted_occupancy_rate,
                    "lower_bound": p.lower_bound,
                    "upper_bound": p.upper_bound,
                }
                for p in self.forecast
            ],
        }


class OccupancyStore:
    def __init__(self, history_limit: int = 288):
        self.history_limit = history_limit
        self.zone_map: Dict[int, ZoneState] = {}
        self.zones_by_type: Dict[str, Set[int]] = defaultdict(set)
        self.zones_by_floor: Dict[str, Set[int]] = defaultdict(set)

    def _type_key(self, zone_type: str) -> str:
        return zone_type.strip().lower()

    def _floor_key(self, floor_label: str) -> str:
        return floor_label.strip().lower()

    def add_zone(
        self,
        zone_id: int,
        zone_name: str,
        floor_label: str,
        zone_type: str,
        capacity: Optional[int] = None,
        library_id: Optional[int] = None,
        is_active: bool = True,
    ) -> ZoneState:
        meta = ZoneMeta(
            zone_id=zone_id,
            zone_name=zone_name,
            floor_label=floor_label,
            zone_type=zone_type,
            capacity=capacity,
            library_id=library_id,
            is_active=is_active,
        )

        if zone_id in self.zone_map:
            old = self.zone_map[zone_id]
            self.zones_by_type[self._type_key(old.meta.zone_type)].discard(zone_id)
            self.zones_by_floor[self._floor_key(old.meta.floor_label)].discard(zone_id)

        state = ZoneState(meta=meta, recent=deque(maxlen=self.history_limit))
        self.zone_map[zone_id] = state
        self.zones_by_type[self._type_key(zone_type)].add(zone_id)
        self.zones_by_floor[self._floor_key(floor_label)].add(zone_id)
        return state

    def remove_zone(self, zone_id: int) -> bool:
        state = self.zone_map.pop(zone_id, None)
        if not state:
            return False
        self.zones_by_type[self._type_key(state.meta.zone_type)].discard(zone_id)
        self.zones_by_floor[self._floor_key(state.meta.floor_label)].discard(zone_id)
        return True

    def get_zone(self, zone_id: int) -> Optional[ZoneState]:
        return self.zone_map.get(zone_id)

    def update_snapshot(
        self,
        zone_id: int,
        occupied_count: int,
        observed_at: Optional[datetime] = None,
        available_count: Optional[int] = None,
        occupancy_rate: Optional[float] = None,
        source_type: str = "manual",
        confidence_score: Optional[float] = None,
    ) -> Snapshot:
        if zone_id not in self.zone_map:
            raise KeyError(f"zone_id {zone_id} not found")

        state = self.zone_map[zone_id]
        capacity = state.meta.capacity

        if available_count is None and capacity is not None:
            available_count = max(0, capacity - occupied_count)

        if occupancy_rate is None:
            occupancy_rate = _safe_rate(occupied_count, capacity)

        snapshot = Snapshot(
            observed_at=observed_at or datetime.now(),
            occupied_count=occupied_count,
            available_count=available_count,
            occupancy_rate=occupancy_rate,
            source_type=source_type,
            confidence_score=confidence_score,
        )

        state.current = snapshot
        state.recent.append(snapshot)
        return snapshot

    def set_forecast(self, zone_id: int, forecast_points: List[ForecastPoint]) -> None:
        if zone_id not in self.zone_map:
            raise KeyError(f"zone_id {zone_id} not found")
        forecast_points.sort(key=lambda x: x.forecast_for)
        self.zone_map[zone_id].forecast = forecast_points

    def append_forecast_point(self, zone_id: int, point: ForecastPoint) -> None:
        if zone_id not in self.zone_map:
            raise KeyError(f"zone_id {zone_id} not found")
        state = self.zone_map[zone_id]
        state.forecast.append(point)
        state.forecast.sort(key=lambda x: x.forecast_for)

    def get_current_snapshot(self, zone_id: int) -> Optional[Snapshot]:
        state = self.zone_map.get(zone_id)
        return state.current if state else None

    def get_recent_snapshots(self, zone_id: int, limit: Optional[int] = None) -> List[Snapshot]:
        state = self.zone_map.get(zone_id)
        if not state:
            return []
        if limit is None or limit >= len(state.recent):
            return list(state.recent)
        return list(state.recent)[-limit:]

    def filter_zone_ids(
        self,
        study_preference: Optional[str] = None,
        preferred_floor: Optional[str] = None,
        active_only: bool = True,
    ) -> List[int]:
        study_preference = _normalize_pref(study_preference)
        preferred_floor = _normalize_pref(preferred_floor)

        candidate_ids: Optional[Set[int]] = None

        if study_preference:
            type_ids = set(self.zones_by_type.get(self._type_key(study_preference), set()))
            candidate_ids = type_ids

        if preferred_floor:
            floor_ids = set(self.zones_by_floor.get(self._floor_key(preferred_floor), set()))
            candidate_ids = floor_ids if candidate_ids is None else candidate_ids & floor_ids

        if candidate_ids is None:
            candidate_ids = set(self.zone_map.keys())

        if active_only:
            candidate_ids = {
                zid for zid in candidate_ids
                if zid in self.zone_map and self.zone_map[zid].meta.is_active
            }

        return sorted(candidate_ids)

    def filter_zones(
        self,
        study_preference: Optional[str] = None,
        preferred_floor: Optional[str] = None,
        active_only: bool = True,
    ) -> List[ZoneState]:
        ids = self.filter_zone_ids(
            study_preference=study_preference,
            preferred_floor=preferred_floor,
            active_only=active_only,
        )
        return [self.zone_map[zid] for zid in ids]

    def recommend(
        self,
        study_preference: Optional[str] = None,
        preferred_floor: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Recommendation]:
        candidates = self.filter_zones(
            study_preference=study_preference,
            preferred_floor=preferred_floor,
            active_only=True,
        )

        scored: List[Recommendation] = []

        for state in candidates:
            current_rate = state.current_rate()
            forecast_rate = state.forecast_rate()

            current_part = current_rate if current_rate is not None else 1.0
            forecast_part = forecast_rate if forecast_rate is not None else current_part

            score = 0.7 * current_part + 0.3 * forecast_part

            occupied = state.current.occupied_count if state.current else None
            available = state.current.available_count if state.current else None

            reason_parts = []
            if current_rate is not None:
                reason_parts.append(f"目前使用率 {current_rate:.1%}")
            if forecast_rate is not None:
                reason_parts.append(f"短期預測使用率 {forecast_rate:.1%}")
            if available is not None:
                reason_parts.append(f"可用座位 {available}")

            reason = "，".join(reason_parts) if reason_parts else "缺少即時資料，按預設規則排序"

            scored.append(
                Recommendation(
                    zone_id=state.meta.zone_id,
                    zone_name=state.meta.zone_name,
                    floor_label=state.meta.floor_label,
                    zone_type=state.meta.zone_type,
                    score=score,
                    current_rate=current_rate,
                    forecast_rate=forecast_rate,
                    occupied_count=occupied,
                    available_count=available,
                    reason=reason,
                )
            )

        scored.sort(key=lambda x: (x.score, -(x.available_count or 0), x.zone_id))
        return scored[:max(0, top_k)]

    def system_summary(self) -> dict:
        total_zones = len(self.zone_map)
        active_zones = sum(1 for z in self.zone_map.values() if z.meta.is_active)

        total_capacity = 0
        total_occupied = 0
        known_capacity = False

        for state in self.zone_map.values():
            if state.meta.capacity is not None:
                known_capacity = True
                total_capacity += state.meta.capacity
            if state.current:
                total_occupied += state.current.occupied_count

        overall_rate = None
        if known_capacity and total_capacity > 0:
            overall_rate = total_occupied / total_capacity

        return {
            "total_zones": total_zones,
            "active_zones": active_zones,
            "total_capacity": total_capacity if known_capacity else None,
            "total_occupied": total_occupied,
            "overall_occupancy_rate": overall_rate,
        }

    def export_state(self) -> dict:
        return {
            "summary": self.system_summary(),
            "zones": [state.to_dict() for _, state in sorted(self.zone_map.items())],
        }


if __name__ == "__main__":
    store = OccupancyStore(history_limit=288)

    store.add_zone(
        zone_id=1,
        zone_name="Quiet Zone A",
        floor_label="2F",
        zone_type="quiet",
        capacity=120,
    )
    store.add_zone(
        zone_id=2,
        zone_name="Discussion Zone",
        floor_label="3F",
        zone_type="discussion",
        capacity=80,
    )
    store.add_zone(
        zone_id=3,
        zone_name="Quiet Zone B",
        floor_label="3F",
        zone_type="quiet",
        capacity=60,
    )

    store.update_snapshot(zone_id=1, occupied_count=52, source_type="sensor")
    store.update_snapshot(zone_id=2, occupied_count=61, source_type="sensor")
    store.update_snapshot(zone_id=3, occupied_count=18, source_type="sensor")

    store.set_forecast(
        1,
        [
            ForecastPoint(datetime.now(), 58, 58 / 120, 50, 65),
            ForecastPoint(datetime.now(), 62, 62 / 120, 54, 70),
        ],
    )
    store.set_forecast(
        3,
        [
            ForecastPoint(datetime.now(), 20, 20 / 60, 16, 26),
            ForecastPoint(datetime.now(), 24, 24 / 60, 18, 30),
        ],
    )

    recs = store.recommend(study_preference="quiet", preferred_floor="3F", top_k=2)

    print("=== Summary ===")
    print(store.system_summary())
    print("\n=== Recommendations ===")
    for r in recs:
        print(r)