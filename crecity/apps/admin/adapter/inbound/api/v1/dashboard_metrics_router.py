from fastapi import APIRouter, Depends

from admin.adapter.inbound.api.schemas.dashboard_metrics_schema import (
    DashboardMetricsResponseSchema,
)
from admin.app.ports.input.dashboard_metrics_use_case import DashboardMetricsUseCase
from admin.dependencies.dashboard_metrics_provider import get_dashboard_metrics_use_case
from hub.dependencies.current_user_provider import require_permission

dashboard_metrics_router = APIRouter(prefix="/admin", tags=["admin"])

# 운영 전반 수치(매출 포함)라 전용 권한을 둔다 — 심사·인출 권한과 분리
_viewer = require_permission("dashboard.view")


@dashboard_metrics_router.get("/dashboard/metrics", response_model=DashboardMetricsResponseSchema)
async def get_dashboard_metrics(
    _actor=Depends(_viewer),
    use_case: DashboardMetricsUseCase = Depends(get_dashboard_metrics_use_case),
) -> DashboardMetricsResponseSchema:
    return DashboardMetricsResponseSchema.from_result(await use_case.get_metrics())
