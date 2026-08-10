from __future__ import annotations

from campaign.app.dtos.herald_dto import HeraldQuery, HeraldResponse
from campaign.app.ports.input.herald_use_case import HeraldUseCase
from campaign.app.ports.output.herald_record_port import HeraldRecordPort


class HeraldInteractor(HeraldUseCase):
    """캠페인 (campaign) 대장 — 담당: 역경매 공고·크리에이터 지원."""

    def __init__(self, record: HeraldRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: HeraldQuery) -> HeraldResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return HeraldResponse(
            id=query.id,
            name=query.name,
            introduction=(
                "역경매를 담당합니다. 제공 엔드포인트: POST /campaign/campaigns(브랜드 공고 등록), "
                "POST /campaign/campaigns/{id}/close(마감), GET /campaign/campaigns(OPEN 목록)·"
                "{id}(상세)·/campaign/my/campaigns(내 공고), "
                "POST·GET /campaign/campaigns/{id}/applications(크리에이터 지원·브랜드 지원자 열람). "
                "예정: 지원 수락 → 주문 연결."
            ),
        )
