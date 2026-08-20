from chat.adapter.outbound.orm.custom_offer_orm import CustomOfferOrm
from chat.domain.entities.custom_offer_entity import CustomOffer, OfferStatus


def to_entity(orm: CustomOfferOrm) -> CustomOffer:
    return CustomOffer(
        id=orm.id,
        conversation_id=orm.conversation_id,
        title=orm.title,
        price_krw=orm.price_krw,
        status=OfferStatus(orm.status),
        revision_limit=orm.revision_limit,
        usage_rights=orm.usage_rights,
        order_id=orm.order_id,
        created_at=orm.created_at,
    )
