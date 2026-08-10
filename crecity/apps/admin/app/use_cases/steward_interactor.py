from __future__ import annotations

from admin.app.dtos.steward_dto import StewardQuery, StewardResponse
from admin.app.ports.input.steward_use_case import StewardUseCase
from admin.app.ports.output.steward_record_port import StewardRecordPort


class StewardInteractor(StewardUseCase):
    """운영 (admin) 대장 — 담당: 프로필 심사·분쟁 중재·운영 대시보드."""

    def __init__(self, record: StewardRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: StewardQuery) -> StewardResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return StewardResponse(
            id=query.id,
            name=query.name,
            introduction=(
                "플랫폼 운영을 담당합니다. 제공 엔드포인트: GET /admin/profiles/pending(심사 대기 목록), "
                "POST /admin/profiles/{id}/approve·reject(심사 결정) — 전부 profile.review 권한(RBAC) "
                "보유자만 접근할 수 있습니다. 심사 상태의 소유자는 creator이며 허브 계약으로만 전이시킵니다. "
                "예정: 분쟁 중재 · 운영 대시보드."
            ),
        )
