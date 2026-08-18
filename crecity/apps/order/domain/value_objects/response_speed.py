"""빠른 응답 배지 판정(갭 #80) — 순수 함수(기준값은 core/config가 소유, 인자로 받는다)."""

from __future__ import annotations


def avg_accept_hours(avg_accept_seconds: float | None) -> float | None:
    """표시용 시간 단위 변환 — 소수 1자리(화면이 다시 계산하지 않게 한 곳에서)."""
    if avg_accept_seconds is None:
        return None
    return round(avg_accept_seconds / 3600, 1)


def is_fast_responder(
    avg_accept_seconds: float | None,
    responded_exits: int,
    expired_exits: int,
    *,
    threshold_hours: int,
    min_samples: int,
) -> bool:
    """빠른 응답 배지 — 표본이 충분하고, 평균 수락이 임계 이내이고, 무응답 만료가 없을 때.

    만료 0건 조건: 빨리 수락하는 주문만 골라 받고 나머지를 방치하는 계정이
    배지를 얻는 것을 막는다. 장기적으로 가혹해지면 기간 윈도우 도입을 검토한다.
    """
    if avg_accept_seconds is None:
        return False
    if responded_exits + expired_exits < min_samples:
        return False
    if expired_exits > 0:
        return False
    return avg_accept_seconds <= threshold_hours * 3600
