from __future__ import annotations

from abc import ABC, abstractmethod

from auth.app.dtos.account_deletion_dto import DeleteAccountCommand


class AccountDeletionUseCase(ABC):
    """계정 삭제(§3.8, 갭 #33) — 활성 주문·잔액이 없어야 한다.

    거래 기록 보존 의무(전자상거래법) 때문에 행을 지우지 않고 식별정보만 익명화한다.
    """

    @abstractmethod
    async def delete(self, command: DeleteAccountCommand) -> None:
        """탈퇴 처리 — 프로필 비활성화·소셜 연결 해제·리프레시 토큰 폐기까지 함께.

        Raises:
            UserNotFoundError: 계정 없음(또는 이미 탈퇴).
            ActiveOrderExistsError: 진행 중 주문이 남아 있음.
            RemainingBalanceError: 잔액(적립금·크레딧)이 남아 있음.
        """
        ...
