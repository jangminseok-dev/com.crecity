from auth.adapter.outbound.orm.social_identity_orm import SocialIdentityOrm
from auth.domain.entities.social_identity_entity import SocialIdentity, SocialProvider


class SocialIdentityMapper:
    """SocialIdentityOrm(영속성) ↔ SocialIdentity(도메인) 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: SocialIdentityOrm) -> SocialIdentity:
        return SocialIdentity(
            id=orm.id,
            user_id=orm.user_id,
            provider=SocialProvider(orm.provider),
            provider_user_id=orm.provider_user_id,
            created_at=orm.created_at,
        )
