from __future__ import annotations

import logging

from auth.app.dtos.gatekeeper_dto import GatekeeperQuery, GatekeeperResponse
from auth.app.ports.input.gatekeeper_use_case import GatekeeperUseCase
from auth.app.ports.output.gatekeeper_record_port import GatekeeperRecordPort

logger = logging.getLogger(__name__)


class GatekeeperInteractor(GatekeeperUseCase):
    """인증 (auth) 대장 — 자기소개 스켈레톤. 담당: 회원 인증·계정 — 크리에이터/브랜드 계정 경계 담당."""

    def __init__(self, record: GatekeeperRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: GatekeeperQuery) -> GatekeeperResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return GatekeeperResponse(
            id=query.id,
            name=query.name,
            introduction="회원 인증을 담당합니다. 현재 제공 엔드포인트는 GET /auth/myself 자기소개뿐입니다. 앞으로 소셜 로그인(카카오·네이버·구글), JWT 발급·검증, 크리에이터/브랜드 계정 구분(동일 이메일 겸용 불가 정책)을 제공할 예정입니다. 아직 토큰 발급 기능은 없습니다.",
        )
