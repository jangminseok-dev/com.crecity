from __future__ import annotations

from notification.app.dtos.bellman_dto import BellmanQuery, BellmanResponse
from notification.app.ports.input.bellman_use_case import BellmanUseCase
from notification.app.ports.output.bellman_record_port import BellmanRecordPort


class BellmanInteractor(BellmanUseCase):
    """알림 (notification) 대장 — 담당: Outbox 릴레이·인앱 알림."""

    def __init__(self, record: BellmanRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: BellmanQuery) -> BellmanResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return BellmanResponse(
            id=query.id,
            name=query.name,
            introduction=(
                "알림을 담당합니다. 제공 엔드포인트: GET /notification/notifications"
                "(내 알림 + 안 읽음 개수), POST /notification/notifications/read-all(모두 읽음). "
                "허브 Outbox의 미발행 이벤트를 워커(scripts/notification_outbox_worker.py)가 "
                "주기 소비해 인앱 알림으로 바꿉니다 — 알림 저장과 발행 마킹은 단일 커밋(중복 방지). "
                "예정: 이메일·알림톡 채널."
            ),
        )
