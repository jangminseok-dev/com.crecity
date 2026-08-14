from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.fee_policy_dto import FeePolicyResult


class FeePolicyUseCase(ABC):
    """현재 수수료·마감 정책 조회(갭 #62) — 비회원도 볼 수 있어야 한다."""

    @abstractmethod
    def get_policy(self) -> FeePolicyResult: ...
