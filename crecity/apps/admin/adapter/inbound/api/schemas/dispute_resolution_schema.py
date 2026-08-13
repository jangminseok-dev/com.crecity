from datetime import datetime

from pydantic import BaseModel


class DisputeSummarySchema(BaseModel):

    id: int
    order_id: int
    package_title: str
    brand_user_id: int
    creator_user_id: int
    amount_krw: int
    brand_total_krw: int
    order_status: str
    raised_by_user_id: int
    reason: str
    status: str
    resolution: str | None
    created_at: datetime | None
