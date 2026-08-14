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
    accepting_orders: bool = True  # 주문 수신 여부(갭 #64)
    created_at: datetime | None
