"""dashboard.view 권한 — 운영 대시보드 지표 조회(갭 #55)

Revision ID: b7c2d4e10a35
Revises: a5fb9e87901a
Create Date: 2026-08-13

스키마 변경 없음 — 권한 데이터만 시드한다(지표는 조회 시점 집계라 테이블이 없다).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b7c2d4e10a35'
down_revision: Union[str, Sequence[str], None] = 'a5fb9e87901a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 권한 시드 — 운영 대시보드 열람(admin 역할에 부여). 매출이 보이므로 별도 권한
    op.execute(
        "INSERT INTO permissions (code, description) "
        "VALUES ('dashboard.view', '운영 대시보드 지표 조회(가입·심사·거래·정산 현황)')"
    )
    op.execute(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id FROM roles r, permissions p "
        "WHERE r.name = 'admin' AND p.code = 'dashboard.view'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id = "
        "(SELECT id FROM permissions WHERE code = 'dashboard.view')"
    )
    op.execute("DELETE FROM permissions WHERE code = 'dashboard.view'")
