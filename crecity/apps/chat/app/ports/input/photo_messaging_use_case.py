from __future__ import annotations

from abc import ABC, abstractmethod

from chat.app.dtos.messaging_dto import MessageResult
from chat.app.dtos.photo_messaging_dto import SendPhotoCommand


class PhotoMessagingUseCase(ABC):
    """사진 메시지 전송 — 결과는 일반 메시지와 같은 형태(MessageResult 공유)."""

    @abstractmethod
    async def send_photo(self, command: SendPhotoCommand) -> MessageResult: ...
