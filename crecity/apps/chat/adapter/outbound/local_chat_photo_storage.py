from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from chat.app.ports.output.chat_photo_storage import ChatPhotoStorage
from core.config import UPLOAD_DIR


class LocalChatPhotoStorage(ChatPhotoStorage):
    """로컬 디스크 저장 — main.py가 같은 디렉토리를 /uploads 정적 경로로 서빙한다."""

    def __init__(self) -> None:
        self._directory = Path(UPLOAD_DIR) / "chat"

    def save(self, content: bytes, extension: str) -> str:
        self._directory.mkdir(parents=True, exist_ok=True)
        file_name = f"{uuid4().hex}.{extension}"
        (self._directory / file_name).write_bytes(content)
        return file_name

    def delete(self, file_name: str) -> None:
        (self._directory / file_name).unlink(missing_ok=True)
