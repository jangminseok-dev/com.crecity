from __future__ import annotations

import logging

from hub.app.dtos.dispatcher_dto import DispatcherQuery, DispatcherResponse
from hub.app.ports.input.dispatcher_use_case import DispatcherUseCase
from hub.app.ports.output.dispatcher_record_port import DispatcherRecordPort

logger = logging.getLogger(__name__)


class DispatcherInteractor(DispatcherUseCase):
    """허브 (hub) 대장 — 자기소개 스켈레톤. 담당: 앱 간 협력의 단일 교차점 — 계약(포트·DTO)만 소유."""

    def __init__(self, record: DispatcherRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: DispatcherQuery) -> DispatcherResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return DispatcherResponse(
            id=query.id,
            name=query.name,
            introduction="앱 간 협력의 단일 교차점입니다. 스포크가 소비할 계약(포트·DTO)을 소유하며, 구체 스포크 패키지는 import하지 않습니다. 현재 공개된 엔드포인트는 GET /hub/myself 자기소개뿐이고, 공개된 교차 협력 계약은 아직 없습니다. 스포크끼리는 직접 통신하지 않고 이 허브의 포트를 경유합니다.",
        )
