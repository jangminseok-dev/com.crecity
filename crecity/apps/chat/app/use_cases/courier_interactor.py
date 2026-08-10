from __future__ import annotations

from chat.app.dtos.courier_dto import CourierQuery, CourierResponse
from chat.app.ports.input.courier_use_case import CourierUseCase
from chat.app.ports.output.courier_record_port import CourierRecordPort


class CourierInteractor(CourierUseCase):
    """채팅 (chat) 대장 — 담당: 주문 전 협상 메시징(분쟁 근거 기록)."""

    def __init__(self, record: CourierRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: CourierQuery) -> CourierResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return CourierResponse(
            id=query.id,
            name=query.name,
            introduction=(
                "협상 메시징을 담당합니다. 제공 엔드포인트: POST /chat/conversations"
                "(브랜드가 크리에이터에게 문의 — 쌍당 1개 재사용), GET /chat/conversations(내 대화 목록), "
                "POST·GET /chat/conversations/{id}/messages(참여자만, 수정·삭제 없음 — 분쟁 근거 보존). "
                "실시간은 주기 폴링 방식입니다. 예정: 안 읽음 표시 · 팀 초대."
            ),
        )
