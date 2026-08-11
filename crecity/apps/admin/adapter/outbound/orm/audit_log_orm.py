from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AdminAuditLogOrm(Base):
    """운영 감사 로그 — append-only(수정·삭제 없음, 갭 #36).

    subject가 곧 기록 종류(profile_review·withdrawal_settlement·steward)라 별도 분류 컬럼을
    두지 않는다. 행위자·대상은 note에 함께 남는다(기록 시점 문장 스냅샷).
    """

    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(String(50), index=True)
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
