from __future__ import annotations

from abc import ABC, abstractmethod

from chat.app.dtos.messaging_dto import MessageResult, MessagesQuery, SendMessageCommand


class MessagingUseCase(ABC):
    """메시지 송수신 유스케이스 — 참여자만, 메시지는 수정·삭제 없음(분쟁 근거)."""

    @abstractmethod
    async def send(self, command: SendMessageCommand) -> MessageResult:
        """메시지를 보낸다.

        Raises:
            ConversationNotFoundError · NotParticipantError(도메인, 403) · ValueError(빈 본문)
        """
        ...

    @abstractmethod
    async def list_messages(self, query: MessagesQuery) -> list[MessageResult]:
        """대화의 메시지 — 오래된 순(최근 100개). 프론트가 주기 폴링한다.

        Raises:
            ConversationNotFoundError · NotParticipantError(도메인, 403)
        """
        ...
