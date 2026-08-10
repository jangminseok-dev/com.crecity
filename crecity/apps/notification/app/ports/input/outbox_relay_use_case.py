from __future__ import annotations

from abc import ABC, abstractmethod

from notification.app.dtos.outbox_relay_dto import RelayResult


class OutboxRelayUseCase(ABC):
    """Outbox 릴레이 유스케이스 — HTTP 표면 없음, 워커 스크립트가 주기 실행한다.

    미발행 이벤트 → 알림 변환(수신자·문구 결정) → 알림 저장+발행 마킹(단일 커밋).
    크래시 시 미발행분은 다음 주기에 재처리된다(유실 없음 — Outbox의 목적).
    """

    @abstractmethod
    async def relay(self) -> RelayResult: ...
