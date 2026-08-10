from auth.adapter.outbound.orm.user_orm import UserOrm
from auth.domain.entities.user_entity import AccountType, User


class UserMapper:
    """UserOrm(영속성) ↔ User(도메인) 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: UserOrm) -> User:
        return User(
            id=orm.id,
            email=orm.email,
            name=orm.name,
            account_type=AccountType(orm.account_type),
            created_at=orm.created_at,
        )
