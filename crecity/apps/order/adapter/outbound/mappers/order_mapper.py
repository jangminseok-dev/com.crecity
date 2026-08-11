from order.adapter.outbound.orm.order_orm import OrderOrm
from order.domain.entities.order_entity import Order, OrderStatus


class OrderMapper:
    """OrderOrm(영속성) ↔ Order(도메인) 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: OrderOrm) -> Order:
        return Order(
            id=orm.id,
            package_id=orm.package_id,
            package_title=orm.package_title,
            brand_user_id=orm.brand_user_id,
            creator_user_id=orm.creator_user_id,
            amount_krw=orm.amount_krw,
            brand_fee_percent=orm.brand_fee_percent,
            creator_fee_percent=orm.creator_fee_percent,
            requirements=orm.requirements,
            status=OrderStatus(orm.status),
            deadline_at=orm.deadline_at,
            cancel_requested_by=orm.cancel_requested_by,
            accept_expired=orm.accept_expired,
            revision_limit=orm.revision_limit,
            revisions_used=orm.revisions_used,
            usage_rights=orm.usage_rights,
            created_at=orm.created_at,
        )
