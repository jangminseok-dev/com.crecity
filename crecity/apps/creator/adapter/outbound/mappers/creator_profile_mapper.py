from creator.adapter.outbound.orm.creator_profile_orm import CreatorProfileOrm
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class CreatorProfileMapper:
    """CreatorProfileOrm(영속성) ↔ CreatorProfile(도메인) 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: CreatorProfileOrm) -> CreatorProfile:
        return CreatorProfile(
            id=orm.id,
            slug=orm.slug,
            name=orm.name,
            tagline=orm.tagline,
            bio=orm.bio,
            location=orm.location,
            primary_category=orm.primary_category,
            status=ProfileStatus(orm.status),
            accepting_orders=orm.accepting_orders,
            rejection_reason=orm.rejection_reason,
            user_id=orm.user_id,
            created_at=orm.created_at,
        )
