from fastapi import APIRouter, Depends, Path

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.monthly_report_schema import MonthlyReportRowSchema
from order.app.dtos.monthly_report_dto import MonthlyReportQuery
from order.app.ports.input.monthly_report_use_case import MonthlyReportUseCase
from order.dependencies.monthly_report_provider import get_monthly_report_use_case

monthly_report_router = APIRouter(prefix="/order", tags=["order"])


@monthly_report_router.get("/reports/{year}", response_model=list[MonthlyReportRowSchema])
async def get_monthly_report(
    year: int = Path(ge=2020, le=2100),
    user: VerifiedUser = Depends(get_current_user),
    use_case: MonthlyReportUseCase = Depends(get_monthly_report_use_case),
) -> list[MonthlyReportRowSchema]:
    """수익·지출 월별 리포트(갭 #90) — **항상 본인 기준**(남의 리포트 조회 불가)."""
    rows = await use_case.report(MonthlyReportQuery(user_id=user.id, year=year))
    return [MonthlyReportRowSchema.from_row(row) for row in rows]
