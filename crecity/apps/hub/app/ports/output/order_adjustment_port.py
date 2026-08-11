from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.order_adjustment_dto import OrderAdjustmentSummary


class OrderAdjustmentPort(ABC):
    """주문 금액 변경 요청 조회·확정 포트 — 구현은 order가 제공하고 main.py가 조립한다.

    §3.8·§6: 진행 중 주문의 증액은 추가 결제(payment)를 거쳐야 에스크로가 맞는다.
    """

    @abstractmethod
    async def get_payable_adjustment(
        self, adjustment_id: int
    ) -> OrderAdjustmentSummary | None:
        """대기 중(REQUESTED) 요청만 반환 — 없거나 이미 처리됐으면 None."""

    @abstractmethod
    async def apply_paid_adjustment(self, adjustment_id: int) -> int | None:
        """추가 결제 완료 반영 — 요청 PAID + 주문 증액 + 예치 기입(단일 트랜잭션).

        반영된 주문 id를 돌려준다. 실패(경합·상태 변화)면 None — payment가 PG 취소로 보정.
        """
