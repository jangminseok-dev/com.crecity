from __future__ import annotations

from abc import ABC, abstractmethod

from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.withdrawal_entity import Withdrawal, WithdrawalStatus


class WithdrawalRepository(ABC):
    """인출 영속성 포트.

    요청 생성은 잔액 재검증·인출 행·차감 기입을 단일 트랜잭션으로 수행한다
    (동시 요청 과인출 방지 — 사용자 단위 잠금은 구현체 몫).
    """

    @abstractmethod
    async def create_if_balance_sufficient(
        self,
        user_id: int,
        amount_krw: int,
        tax_krw: int,
        payout_krw: int,
        bank_name: str,
        account_number: str,
        account_holder: str,
    ) -> Withdrawal | None:
        """잔액이 충분하면 인출 행 + WITHDRAWAL 차감 기입을 원자적으로 생성.

        잔액 부족이면 아무것도 만들지 않고 None.
        """
        ...

    @abstractmethod
    async def find_by_id(self, withdrawal_id: int) -> Withdrawal | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: int) -> list[Withdrawal]:
        """내 인출 내역 — 최신순."""
        ...

    @abstractmethod
    async def list_by_status(self, status: WithdrawalStatus) -> list[Withdrawal]:
        """상태별 목록(운영 처리용) — 오래된 순."""
        ...

    @abstractmethod
    async def list_paid_in_year(self, year: int, user_id: int | None = None) -> list[Withdrawal]:
        """지급 완료(PAID)된 인출 — 지급일(settled_at) 연도 기준, 오래된 순.

        지급명세서(갭 #2)용. user_id를 주면 그 크리에이터 몫만, 없으면 전체(운영 집계).
        """
        ...

    @abstractmethod
    async def save_settlement(
        self, withdrawal: Withdrawal, entries: list[LedgerEntryDraft]
    ) -> Withdrawal:
        """처리 결과(상태·정산 시각)와 복원 기입(실패 시)을 원자적으로 저장한다."""
        ...
