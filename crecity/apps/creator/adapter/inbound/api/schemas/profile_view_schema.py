from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from creator.app.dtos.profile_view_dto import ProfileViewsResult


class DailyViewSchema(BaseModel):

    view_date: date
    view_count: int


class ProfileViewsResponseSchema(BaseModel):

    days: int
    total: int
    daily: list[DailyViewSchema]

    @classmethod
    def from_result(cls, result: ProfileViewsResult) -> ProfileViewsResponseSchema:
        return cls(
            days=result.days,
            total=result.total,
            daily=[
                DailyViewSchema(view_date=row.view_date, view_count=row.view_count)
                for row in result.daily
            ],
        )
