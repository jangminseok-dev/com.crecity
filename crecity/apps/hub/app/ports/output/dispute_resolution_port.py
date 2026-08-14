from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.dispute_resolution_dto import DisputeSummary


class DisputeResolutionPort(ABC):
    """분쟁 판정 포트 — 구현은 order가 제공하고 main.py가 조립한다(갭 #4).

    판정은 전액 단위다: 브랜드 전액 환불(refund) 또는 크리에이터 전액 지급(release),
    그리고 주문을 건드리지 않는 기각(dismiss). 부분 배분은 지원하지 않는다.
    """

    @abstractmethod
    async def list_resolved(self) -> list[DisputeSummary]:
        """판정이 끝난 분쟁 이력(갭 #71) — 최근 판정 순."""
        ...

    @abstractmethod
    async def list_open(self) -> list[DisputeSummary]:
        """처리 대기 분쟁 — 오래된 순."""
        ...

    @abstractmethod
    async def resolve(self, dispute_id: int, resolution: str, operator_user_id: int) -> (
        DisputeSummary | None
    ):
        """판정 확정 — 없으면 None, 이미 처리됐거나 주문 상태가 맞지 않으면 ValueError.

        REFUND·RELEASE는 주문 전이·원장 기입과 단일 트랜잭션으로 저장된다.
        """
        ...
