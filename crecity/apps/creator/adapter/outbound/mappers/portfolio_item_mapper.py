from creator.adapter.outbound.orm.portfolio_item_orm import PortfolioItemOrm
from creator.domain.entities.portfolio_item_entity import PortfolioItem


def to_entity(orm: PortfolioItemOrm) -> PortfolioItem:
    return PortfolioItem(
        id=orm.id,
        profile_id=orm.profile_id,
        file_name=orm.file_name,
        created_at=orm.created_at,
    )
