from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from payment.adapter.outbound.mappers.payment_intent_mapper import PaymentIntentMapper
from payment.adapter.outbound.orm.payment_intent_orm import (
    PaymentIntentItemOrm,
    PaymentIntentOrm,
)
from payment.app.ports.output.payment_intent_repository import PaymentIntentRepository
from payment.domain.entities.payment_intent_entity import PaymentIntent, PaymentIntentStatus


class PaymentIntentPgRepository(PaymentIntentRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        pg_order_id: str,
        package_id: int | None,
        brand_user_id: int,
        requirements: str,
        amount_krw: int,
        offer_id: int | None = None,
        application_id: int | None = None,
        credit_applied_krw: int = 0,
        cart_package_ids: list[int] | None = None,
    ) -> PaymentIntent:
        result = await self._session.execute(
            insert(PaymentIntentOrm)
            .values(
                pg_order_id=pg_order_id,
                package_id=package_id,
                offer_id=offer_id,
                application_id=application_id,
                brand_user_id=brand_user_id,
                requirements=requirements,
                amount_krw=amount_krw,
                credit_applied_krw=credit_applied_krw,
                status=PaymentIntentStatus.READY.value,
            )
            .returning(PaymentIntentOrm)
        )
        orm = result.scalar_one()
        for item_package_id in cart_package_ids or []:
            await self._session.execute(
                insert(PaymentIntentItemOrm).values(
                    intent_id=orm.id, package_id=item_package_id
                )
            )
        await self._session.commit()
        return PaymentIntentMapper.to_entity(orm, tuple(cart_package_ids or ()))

    async def _cart_package_ids(self, intent_id: int) -> tuple[int, ...]:
        result = await self._session.execute(
            select(PaymentIntentItemOrm.package_id)
            .where(PaymentIntentItemOrm.intent_id == intent_id)
            .order_by(PaymentIntentItemOrm.id)
        )
        return tuple(result.scalars())

    async def find_by_pg_order_id(self, pg_order_id: str) -> PaymentIntent | None:
        result = await self._session.execute(
            select(PaymentIntentOrm).where(PaymentIntentOrm.pg_order_id == pg_order_id)
        )
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        return PaymentIntentMapper.to_entity(orm, await self._cart_package_ids(orm.id))

    async def mark_confirmed(self, intent_id: int, payment_key: str, order_id: int) -> None:
        await self._session.execute(
            update(PaymentIntentOrm)
            .where(PaymentIntentOrm.id == intent_id)
            .values(
                status=PaymentIntentStatus.CONFIRMED.value,
                payment_key=payment_key,
                order_id=order_id,
            )
        )
        await self._session.commit()

    async def mark_failed(self, intent_id: int, payment_key: str | None, reason: str) -> None:
        await self._session.execute(
            update(PaymentIntentOrm)
            .where(PaymentIntentOrm.id == intent_id)
            .values(
                status=PaymentIntentStatus.FAILED.value,
                payment_key=payment_key,
                failure_reason=reason[:300],
            )
        )
        await self._session.commit()
