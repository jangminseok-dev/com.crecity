from payment.adapter.outbound.orm.payment_intent_orm import PaymentIntentOrm
from payment.domain.entities.payment_intent_entity import PaymentIntent, PaymentIntentStatus


class PaymentIntentMapper:
    """PaymentIntentOrm(영속성) ↔ PaymentIntent(도메인) 변환을 담당한다."""

    @staticmethod
    def to_entity(
        orm: PaymentIntentOrm, cart_package_ids: tuple[int, ...] = ()
    ) -> PaymentIntent:
        return PaymentIntent(
            cart_package_ids=cart_package_ids,
            id=orm.id,
            pg_order_id=orm.pg_order_id,
            package_id=orm.package_id,
            offer_id=orm.offer_id,
            application_id=orm.application_id,
            brand_user_id=orm.brand_user_id,
            requirements=orm.requirements,
            amount_krw=orm.amount_krw,
            credit_applied_krw=orm.credit_applied_krw,
            status=PaymentIntentStatus(orm.status),
            payment_key=orm.payment_key,
            order_id=orm.order_id,
            failure_reason=orm.failure_reason,
            created_at=orm.created_at,
        )
