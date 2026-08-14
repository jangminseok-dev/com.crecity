from review.adapter.outbound.orm.review_orm import ReviewOrm
from review.domain.entities.review_entity import Review


class ReviewMapper:
    """ReviewOrm(영속성) ↔ Review(도메인) 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: ReviewOrm) -> Review:
        return Review(
            id=orm.id,
            order_id=orm.order_id,
            brand_user_id=orm.brand_user_id,
            creator_user_id=orm.creator_user_id,
            communication_score=orm.communication_score,
            timeliness_score=orm.timeliness_score,
            satisfaction_score=orm.satisfaction_score,
            comment=orm.comment,
            created_at=orm.created_at,
            reply=orm.reply,
            replied_at=orm.replied_at,
        )
