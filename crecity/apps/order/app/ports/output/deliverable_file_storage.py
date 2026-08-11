from abc import ABC, abstractmethod


class DeliverableFileStorage(ABC):
    """납품물 파일 저장 포트 — append-only 기록이므로 삭제는 제공하지 않는다."""

    @abstractmethod
    def save(self, content: bytes, extension: str) -> str:
        """파일을 저장하고 저장 파일명을 반환한다."""
        ...
