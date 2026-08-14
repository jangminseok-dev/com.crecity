from fastapi import APIRouter, Depends, HTTPException

from admin.adapter.inbound.api.schemas.dispute_resolution_schema import DisputeSummarySchema
from admin.app.dtos.dispute_resolution_dto import DisputeDecisionCommand
from admin.app.exceptions import DisputeTargetNotFoundError
from admin.app.ports.input.dispute_resolution_use_case import DisputeResolutionUseCase
from admin.dependencies.dispute_resolution_provider import get_dispute_resolution_use_case
from hub.app.dtos.dispute_resolution_dto import DisputeSummary
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import require_permission

dispute_resolution_router = APIRouter(prefix="/admin", tags=["admin"])

_arbiter = require_permission("dispute.resolve")


def _to_schema(summary: DisputeSummary) -> DisputeSummarySchema:
    return DisputeSummarySchema(
        id=summary.id,
        order_id=summary.order_id,
        package_title=summary.package_title,
        brand_user_id=summary.brand_user_id,
        creator_user_id=summary.creator_user_id,
        amount_krw=summary.amount_krw,
        brand_total_krw=summary.brand_total_krw,
        order_status=summary.order_status,
        raised_by_user_id=summary.raised_by_user_id,
        reason=summary.reason,
        status=summary.status,
        resolution=summary.resolution,
        created_at=summary.created_at,
    )


@dispute_resolution_router.get("/disputes/open", response_model=list[DisputeSummarySchema])
async def list_open_disputes(
    user: VerifiedUser = Depends(_arbiter),
    use_case: DisputeResolutionUseCase = Depends(get_dispute_resolution_use_case),
) -> list[DisputeSummarySchema]:
    return [_to_schema(summary) for summary in await use_case.list_open()]


@dispute_resolution_router.get("/disputes/resolved", response_model=list[DisputeSummarySchema])
async def list_resolved_disputes(
    user: VerifiedUser = Depends(_arbiter),
    use_case: DisputeResolutionUseCase = Depends(get_dispute_resolution_use_case),
) -> list[DisputeSummarySchema]:
    """판정 완료 이력(갭 #71) — 최근 판정부터. 운영 인수인계·재발 확인용."""
    return [_to_schema(summary) for summary in await use_case.list_resolved()]


async def _resolve(
    dispute_id: int,
    resolution: str,
    user: VerifiedUser,
    use_case: DisputeResolutionUseCase,
) -> DisputeSummarySchema:
    try:
        result = await use_case.resolve(
            DisputeDecisionCommand(
                dispute_id=dispute_id,
                resolution=resolution,
                operator_id=user.id,
                operator_email=user.email,
            )
        )
    except DisputeTargetNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return _to_schema(result)


@dispute_resolution_router.post(
    "/disputes/{dispute_id}/refund", response_model=DisputeSummarySchema
)
async def refund_dispute(
    dispute_id: int,
    user: VerifiedUser = Depends(_arbiter),
    use_case: DisputeResolutionUseCase = Depends(get_dispute_resolution_use_case),
) -> DisputeSummarySchema:
    """브랜드 전액 환불(크레딧) — 주문은 취소된다."""
    return await _resolve(dispute_id, "REFUND", user=user, use_case=use_case)


@dispute_resolution_router.post(
    "/disputes/{dispute_id}/release", response_model=DisputeSummarySchema
)
async def release_dispute(
    dispute_id: int,
    user: VerifiedUser = Depends(_arbiter),
    use_case: DisputeResolutionUseCase = Depends(get_dispute_resolution_use_case),
) -> DisputeSummarySchema:
    """크리에이터 전액 지급 — 구매 확정과 같은 기입."""
    return await _resolve(dispute_id, "RELEASE", user=user, use_case=use_case)


@dispute_resolution_router.post(
    "/disputes/{dispute_id}/dismiss", response_model=DisputeSummarySchema
)
async def dismiss_dispute(
    dispute_id: int,
    user: VerifiedUser = Depends(_arbiter),
    use_case: DisputeResolutionUseCase = Depends(get_dispute_resolution_use_case),
) -> DisputeSummarySchema:
    """기각 — 주문 상태를 바꾸지 않고 분쟁만 닫는다."""
    return await _resolve(dispute_id, "DISMISS", user=user, use_case=use_case)
