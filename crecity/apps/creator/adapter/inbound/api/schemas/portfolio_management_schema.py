from datetime import datetime

from pydantic import BaseModel


class PortfolioItemResponseSchema(BaseModel):

    id: int
    image_url: str  # 정적 서빙 경로(/uploads/portfolio/...) — 프론트는 그대로 <img src>
    created_at: datetime | None
