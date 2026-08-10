from __future__ import annotations

import logging

from creator.app.dtos.profile_dto import ProfileQuery, ProfileResponse
from creator.app.ports.input.profile_use_case import ProfileUseCase
from creator.app.ports.output.profile_record_port import ProfileRecordPort

logger = logging.getLogger(__name__)


class ProfileInteractor(ProfileUseCase):
    """크리에이터 (creator) 대장 — 자기소개 스켈레톤. 담당: 크리에이터 프로필·판매 패키지 — 마켓플레이스 공급 측 상품 단위."""

    def __init__(self, record: ProfileRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: ProfileQuery) -> ProfileResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return ProfileResponse(
            id=query.id,
            name=query.name,
            introduction="크리에이터 프로필과 판매 패키지를 담당합니다. 현재 제공 엔드포인트는 GET /creator/myself 자기소개뿐입니다. 앞으로 프로필 등록·심사 상태 관리, 가격 공개 패키지 CRUD, 크리에이터별 고유 슬러그 URL 조회(프로그래매틱 SEO 단위)를 제공할 예정입니다. 결제·주문은 이 앱이 아니라 주문 도메인 몫입니다.",
        )
