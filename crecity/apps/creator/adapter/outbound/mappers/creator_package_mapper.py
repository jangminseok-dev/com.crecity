from creator.adapter.outbound.orm.creator_package_orm import CreatorPackageOrm
from creator.domain.entities.creator_package_entity import CreatorPackage, PackagePlatform


class CreatorPackageMapper:
    """CreatorPackageOrm(영속성) ↔ CreatorPackage(도메인) 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: CreatorPackageOrm) -> CreatorPackage:
        return CreatorPackage(
            id=orm.id,
            profile_id=orm.profile_id,
            platform=PackagePlatform(orm.platform),
            title=orm.title,
            description=orm.description,
            price_krw=orm.price_krw,
            revision_limit=orm.revision_limit,
            usage_rights=orm.usage_rights,
            created_at=orm.created_at,
        )
