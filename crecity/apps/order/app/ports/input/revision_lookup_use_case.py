from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.revision_lookup_dto import RevisionListQuery, RevisionRequestResult


class RevisionLookupUseCase(ABC):
    """수정 요청 이력 조회(갭 #84).

    Raises:
        OrderNotFoundError: 주문 없음.
        NotOrderParticipantError: 당사자 아님.
    """

    @abstractmethod
    async def list_revisions(self, query: RevisionListQuery) -> list[RevisionRequestResult]: ...
