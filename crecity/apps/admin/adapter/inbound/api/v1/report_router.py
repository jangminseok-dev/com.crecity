from fastapi import APIRouter, Depends, HTTPException

from admin.adapter.inbound.api.schemas.report_schema import (
    ReportResolveRequestSchema,
    ReportResponseSchema,
    ReportSubmissionRequestSchema,
)
from admin.app.dtos.report_dto import ReportResolveCommand, ReportSubmissionCommand
from admin.app.exceptions import DuplicateReportError, ReportTargetNotFoundError
from admin.app.ports.input.report_review_use_case import ReportReviewUseCase
from admin.app.ports.input.report_submission_use_case import ReportSubmissionUseCase
from admin.dependencies.report_provider import (
    get_report_review_use_case,
    get_report_submission_use_case,
)
from admin.domain.entities.report_entity import (
    InvalidReasonError,
    ReportAlreadyResolvedError,
)
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user, require_permission

report_router = APIRouter(prefix="/admin", tags=["admin"])

# 처리·열람은 운영 권한자만. 접수(POST /admin/reports)는 예외적으로 로그인 사용자에게 열린다
# — 어뷰징을 당한 당사자가 내는 창구이기 때문이다.
_handler = require_permission("report.review")


@report_router.post("/reports", response_model=ReportResponseSchema, status_code=201)
async def submit_report(
    body: ReportSubmissionRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: ReportSubmissionUseCase = Depends(get_report_submission_use_case),
) -> ReportResponseSchema:
    """어뷰징 신고 접수(갭 #54) — 로그인 사용자면 누구나."""
    try:
        result = await use_case.submit(
            ReportSubmissionCommand(
                reporter_user_id=user.id,
                target_type=body.target_type.value,
                target_id=body.target_id,
                reason=body.reason,
            )
        )
    except InvalidReasonError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except DuplicateReportError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return ReportResponseSchema.from_result(result)


@report_router.get("/reports/open", response_model=list[ReportResponseSchema])
async def list_open_reports(
    _actor=Depends(_handler),
    use_case: ReportReviewUseCase = Depends(get_report_review_use_case),
) -> list[ReportResponseSchema]:
    results = await use_case.list_reports()
    return [ReportResponseSchema.from_result(result) for result in results]


@report_router.get("/reports/resolved", response_model=list[ReportResponseSchema])
async def list_resolved_reports(
    _actor=Depends(_handler),
    use_case: ReportReviewUseCase = Depends(get_report_review_use_case),
) -> list[ReportResponseSchema]:
    """처리 완료 이력(갭 #71) — 최근 판단부터. 운영 인수인계·재발 확인용."""
    results = await use_case.list_reports(resolved=True)
    return [ReportResponseSchema.from_result(result) for result in results]


@report_router.post("/reports/{report_id}/resolve", response_model=ReportResponseSchema)
async def resolve_report(
    report_id: int,
    body: ReportResolveRequestSchema,
    actor: VerifiedUser = Depends(_handler),
    use_case: ReportReviewUseCase = Depends(get_report_review_use_case),
) -> ReportResponseSchema:
    """신고 처리 — 조치 내용을 메모로 남기고 닫는다(조치 자체는 별도 기능으로)."""
    try:
        result = await use_case.resolve(
            ReportResolveCommand(
                report_id=report_id, resolver_user_id=actor.id, note=body.note
            )
        )
    except ReportTargetNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ReportAlreadyResolvedError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return ReportResponseSchema.from_result(result)
