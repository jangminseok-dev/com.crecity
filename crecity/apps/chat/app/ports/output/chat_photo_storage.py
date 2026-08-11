from abc import ABC, abstractmethod


class ChatPhotoStorage(ABC):
    """채팅 사진 파일 저장소 — 로컬 디스크로 시작, 오브젝트 스토리지 전환 시 구현체만 교체."""

    @abstractmethod
    def save(self, content: bytes, extension: str) -> str:
        """저장 후 생성된 파일명 반환(이름 충돌 없는 무작위 생성은 구현체 몫)."""

    @abstractmethod
    def delete(self, file_name: str) -> None:
        """파일 삭제 — 이미 없으면 조용히 무시(DB가 정본)."""
