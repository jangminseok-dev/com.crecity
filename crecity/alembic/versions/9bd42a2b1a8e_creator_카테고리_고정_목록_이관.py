"""creator: 카테고리 고정 목록 이관

Revision ID: 9bd42a2b1a8e
Revises: bbd5c4b535f9
Create Date: 2026-08-11 12:01:10.503542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bd42a2b1a8e'
down_revision: Union[str, Sequence[str], None] = 'bbd5c4b535f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """카테고리 고정 목록 이관 — 개발→테크, 그 외 목록 밖 값은 라이프로."""
    categories = "('뷰티','패션','푸드','여행','테크','피트니스','라이프','포토','영상')"
    op.execute("UPDATE creator_profiles SET primary_category = '테크' WHERE primary_category = '개발'")
    op.execute(
        f"UPDATE creator_profiles SET primary_category = '라이프' WHERE primary_category NOT IN {categories}"
    )


def downgrade() -> None:
    """데이터 이관이라 되돌리지 않는다(원본 값 미보존)."""
    pass
