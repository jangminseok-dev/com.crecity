from dataclasses import dataclass


@dataclass(frozen=True)
class CreatorResponseStats:
    """크리에이터 응답 통계(갭 #80) — 전이 이력(갭 #79) 기반 집계.

    수락 대기(PENDING_ACCEPT)를 벗어난 전이만 표본이다 — 도입 이전 주문은 이력이 없어
    집계에 들어오지 않는다(소급 불가).
    """

    avg_accept_seconds: float | None  # 주문 생성 → 수락 평균 소요(수락된 주문만) — 없으면 None
    responded_exits: int  # 수락 또는 거절로 응답한 건수
    expired_exits: int  # 무응답 만료로 끝난 건수
