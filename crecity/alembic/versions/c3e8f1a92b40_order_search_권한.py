"""order.search 권한 — 운영 주문 검색(갭 #56)

Revision ID: c3e8f1a92b40
Revises: b7c2d4e10a35
Create Date: 2026-08-13

스키마 변경 없음 — 권한 데이터만 시드한다(검색은 order 테이블 읽기 전용).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3e8f1a92b40'
down_revision: Union[str, Sequence[str], None] = 'b7c2d4e10a35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 권한 시드 — 남의 주문 내역 조회라 별도 권한(admin 역할에 부여)
    op.execute(
        "INSERT INTO permissions (code, description) "
        "VALUES ('order.search', '운영 주문 검색(문의 대응용 조회)')"
    )
    op.execute(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id FROM roles r, permissions p "
        "WHERE r.name = 'admin' AND p.code = 'order.search'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id = "
        "(SELECT id FROM permissions WHERE code = 'order.search')"
    )
    op.execute("DELETE FROM permissions WHERE code = 'order.search'")
