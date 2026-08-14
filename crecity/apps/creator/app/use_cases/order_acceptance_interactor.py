from __future__ import annotations

from creator.app.dtos.order_acceptance_dto import (
    OrderAcceptanceCommand,
    OrderAcceptanceResult,
)
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.order_acceptance_use_case import OrderAcceptanceUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository


class OrderAcceptanceInteractor(OrderAcceptanceUseCase):

    def __init__(self, repository: CreatorProfileRepository) -> None:
        self._repository = repository

    async def set_accepting(self, command: OrderAcceptanceCommand) -> OrderAcceptanceResult:
        # 진행 중인 주문에는 영향이 없다 — 새 주문만 막는다
        profile = await self._repository.set_accepting_orders(
            user_id=command.user_id, accepting=command.accepting
        )
        if profile is None:
            raise ProfileNotFoundError("등록된 프로필이 없습니다.")
        return OrderAcceptanceResult(
            slug=profile.slug, accepting_orders=profile.accepting_orders
        )
