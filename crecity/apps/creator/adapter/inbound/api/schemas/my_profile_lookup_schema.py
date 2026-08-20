from datetime import datetime

from pydantic import BaseModel


class MyProfileResponseSchema(BaseModel):

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str
    status: str
    # 기본값을 두지 않는다 — 라우터가 빠뜨리면 조용히 True가 되어 실제 값을 덮는다
    accepting_orders: bool
    rejection_reason: str | None  # 반려 사유(갭 #101) — 기본값 없이 라우터가 명시적으로 채운다
    created_at: datetime | None
