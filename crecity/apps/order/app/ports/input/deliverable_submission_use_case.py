from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.deliverable_submission_dto import (
    DeliverableListQuery,
    DeliverableResult,
    SubmitDeliverableFileCommand,
    SubmitDeliverableLinkCommand,
)


class DeliverableSubmissionUseCase(ABC):
    """납품물 등록·열람 유스케이스 — 등록 가능 조건은 도메인(Order)이 강제한다.

    등록 공통 Raises:
        OrderNotFoundError: 주문 없음.
        NotOrderActorError: 주문을 받은 크리에이터가 아님.
        InvalidOrderTransitionError: IN_PROGRESS 상태가 아님.
        ValueError: 파일 형식·크기 또는 링크 형식 위반.
    """

    @abstractmethod
    async def submit_file(self, command: SubmitDeliverableFileCommand) -> DeliverableResult:
        """파일 납품물 등록 — 저장 후 append-only 기록."""
        ...

    @abstractmethod
    async def submit_link(self, command: SubmitDeliverableLinkCommand) -> DeliverableResult:
        """링크 납품물 등록 (게시된 콘텐츠 URL 등)."""
        ...

    @abstractmethod
    async def list_deliverables(self, query: DeliverableListQuery) -> list[DeliverableResult]:
        """주문의 납품물 목록(등록순) — 당사자만.

        Raises:
            OrderNotFoundError: 주문 없음.
            NotOrderParticipantError: 주문 당사자가 아님.
        """
        ...
