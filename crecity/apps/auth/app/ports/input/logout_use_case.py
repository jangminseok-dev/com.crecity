from __future__ import annotations

from abc import ABC, abstractmethod

from auth.app.dtos.logout_dto import LogoutCommand


class LogoutUseCase(ABC):
    """로그아웃 유스케이스 — 서버 측 리프레시 토큰 폐기(갭 #5-1).

    쿠키 삭제만으로는 토큰이 14일간 유효하므로 저장소에서 즉시 지운다.
    """

    @abstractmethod
    async def logout(self, command: LogoutCommand) -> None:
        """리프레시 토큰을 폐기한다 — 이미 없어도 성공(멱등)."""
        ...
