from __future__ import annotations

from datetime import datetime, timezone

from core.database import session_scope
from hub.app.dtos.dispute_resolution_dto import DisputeSummary
from hub.app.ports.output.dispute_resolution_port import DisputeResolutionPort
from order.adapter.outbound.pg.dispute_pg_repository import DisputePgRepository
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.events import order_event
from order.domain.entities.dispute_entity import (
    Dispute,
    DisputeResolution,
    DisputeStatus,
    InvalidDisputeStateError,
)
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.order_entity import InvalidOrderTransitionError, Order


def _to_summary(dispute: Dispute, order: Order) -> DisputeSummary:
    return DisputeSummary(
        id=dispute.id,
        order_id=dispute.order_id,
        package_title=order.package_title,
        brand_user_id=order.brand_user_id,
        creator_user_id=order.creator_user_id,
        amount_krw=order.amount_krw,
        brand_total_krw=order.brand_total_krw(),
        order_status=order.status.value,
        raised_by_user_id=dispute.raised_by_user_id,
        reason=dispute.reason,
        status=dispute.status.value,
        resolution=dispute.resolution.value if dispute.resolution else None,
        created_at=dispute.created_at,
    )


def _apply(
    order: Order, resolution: DisputeResolution
) -> tuple[Order | None, list[LedgerEntryDraft]]:
    """판정에 따른 주문 전이 — 기각은 주문을 건드리지 않는다."""
    if resolution is DisputeResolution.REFUND:
        return order.resolve_dispute_refund()
    if resolution is DisputeResolution.RELEASE:
        return order.resolve_dispute_release()
    return None, []


class OrderDisputeResolutionGateway(DisputeResolutionPort):
    """허브 DisputeResolutionPort 계약의 order 구현 — main.py가 조립한다."""

    async def list_open(self) -> list[DisputeSummary]:
        return await self._list(DisputeStatus.OPEN)

    async def list_resolved(self) -> list[DisputeSummary]:
        return await self._list(DisputeStatus.RESOLVED)

    async def _list(self, status: DisputeStatus) -> list[DisputeSummary]:
        async with session_scope() as session:
            disputes = await DisputePgRepository(session).list_by_status(status)
            orders = OrderPgRepository(session)
            summaries = []
            for dispute in disputes:
                order = await orders.find_by_id(dispute.order_id)
                if order is not None:
                    summaries.append(_to_summary(dispute, order))
        return summaries

    async def resolve(
        self, dispute_id: int, resolution: str, operator_user_id: int
    ) -> DisputeSummary | None:
        try:
            decision = DisputeResolution(resolution)
        except ValueError:
            raise ValueError(f"알 수 없는 판정입니다: {resolution}")

        async with session_scope() as session:
            repository = DisputePgRepository(session)
            dispute = await repository.find_by_id(dispute_id)
            if dispute is None:
                return None
            order = await OrderPgRepository(session).find_by_id(dispute.order_id)
            if order is None:
                return None
            try:
                resolved = dispute.resolve(
                    decision, operator_user_id, datetime.now(timezone.utc)
                )
                transitioned, entries = _apply(order, decision)
            except (InvalidDisputeStateError, InvalidOrderTransitionError) as error:
                raise ValueError(str(error))

            events = [
                order_event("order.dispute_resolved", order, resolution=decision.value)
            ]
            await repository.resolve(resolved, transitioned, entries, events)
        return _to_summary(resolved, transitioned or order)
