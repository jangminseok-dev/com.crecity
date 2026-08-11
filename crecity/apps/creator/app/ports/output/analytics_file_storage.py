from abc import ABC, abstractmethod


class AnalyticsFileStorage(ABC):
    """인증 스크린샷 저장 포트."""

    @abstractmethod
    def save(self, content: bytes, extension: str) -> str:
        """파일을 저장하고 저장 파일명을 반환한다."""
        ...
