"""인출 처리 결과 이벤트 빌더(갭 #74) — 정산 게이트웨이가 쓴다.

이벤트는 상태 변경·원장 기입과 같은 트랜잭션에 적재된다(BOUNDARIES §1).
**돈이 오가는 사건**이라 공백이 크다 — 실패 시 잔액 복원도 조용히 일어난다.
"""

from __future__ import annotations

from hub.app.dtos.outbox_event_dto import OutboxEvent
from order.domain.entities.withdrawal_entity import Withdrawal


def withdrawal_event(event_type: str, withdrawal: Withdrawal) -> OutboxEvent:
    return OutboxEvent(
        event_type=event_type,
        payload={
            "withdrawal_id": withdrawal.id,
            "creator_user_id": withdrawal.user_id,
            "amount_krw": withdrawal.amount_krw,
            "payout_krw": withdrawal.payout_krw,
        },
    )
