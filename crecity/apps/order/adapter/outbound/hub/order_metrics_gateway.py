from __future__ import annotations

from sqlalchemy import func, select

from core.database import session_scope
from hub.app.dtos.platform_metrics_dto import OrderMetrics
from hub.app.ports.output.platform_metrics_port import OrderMetricsPort
from order.adapter.outbound.orm.dispute_orm import DisputeOrm
from order.adapter.outbound.orm.ledger_entry_orm import LedgerEntryOrm
from order.adapter.outbound.orm.order_orm import OrderOrm
from order.adapter.outbound.orm.withdrawal_orm import WithdrawalOrm
from order.domain.entities.dispute_entity import DisputeStatus
from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import OrderStatus
from order.domain.entities.withdrawal_entity import WithdrawalStatus


class OrderMetricsGateway(OrderMetricsPort):
    """허브 OrderMetricsPort 계약의 order 구현(운영 대시보드, 갭 #55).

    수수료 수입은 다시 계산하지 않고 **원장의 PLATFORM_REVENUE 합**을 읽는다 —
    원장이 진실의 원천이고(BOUNDARIES §3), 도메인의 내림 계산을 SQL로 복제하면 어긋난다.
    """

    async def get_order_metrics(self) -> OrderMetrics:
        async with session_scope() as session:
            status_rows = await session.execute(
                select(OrderOrm.status, func.count()).group_by(OrderOrm.status)
            )
            by_status = {status: int(count) for status, count in status_rows.all()}

            gmv = await session.scalar(
                select(func.coalesce(func.sum(OrderOrm.amount_krw), 0)).where(
                    OrderOrm.status == OrderStatus.COMPLETED.value
                )
            )
            revenue = await session.scalar(
                select(func.coalesce(func.sum(LedgerEntryOrm.amount_krw), 0)).where(
                    LedgerEntryOrm.entry_type == LedgerEntryType.PLATFORM_REVENUE.value
                )
            )
            open_disputes = await session.scalar(
                select(func.count())
                .select_from(DisputeOrm)
                .where(DisputeOrm.status == DisputeStatus.OPEN.value)
            )
            # 인출 대기 금액은 운영자가 실제로 이체할 금액(원천징수 뒤 실지급액)
            withdrawal_row = await session.execute(
                select(func.count(), func.coalesce(func.sum(WithdrawalOrm.payout_krw), 0)).where(
                    WithdrawalOrm.status == WithdrawalStatus.REQUESTED.value
                )
            )
            withdrawal_count, withdrawal_krw = withdrawal_row.one()

        return OrderMetrics(
            pending_accept=by_status.get(OrderStatus.PENDING_ACCEPT.value, 0),
            in_progress=by_status.get(OrderStatus.IN_PROGRESS.value, 0),
            in_review=by_status.get(OrderStatus.IN_REVIEW.value, 0),
            completed=by_status.get(OrderStatus.COMPLETED.value, 0),
            refunded=by_status.get(OrderStatus.REFUNDED.value, 0),
            cancelled=by_status.get(OrderStatus.CANCELLED.value, 0),
            gmv_krw=int(gmv or 0),
            platform_revenue_krw=int(revenue or 0),
            open_disputes=int(open_disputes or 0),
            pending_withdrawals=int(withdrawal_count),
            pending_withdrawal_krw=int(withdrawal_krw),
        )
