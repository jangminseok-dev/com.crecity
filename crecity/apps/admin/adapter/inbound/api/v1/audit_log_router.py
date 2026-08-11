from fastapi import APIRouter, Depends

from admin.adapter.inbound.api.schemas.audit_log_schema import AuditLogResponseSchema
from admin.app.ports.input.audit_log_lookup_use_case import AuditLogLookupUseCase
from admin.dependencies.audit_log_lookup_provider import get_audit_log_lookup_use_case
from hub.dependencies.current_user_provider import require_permission

audit_log_router = APIRouter(prefix="/admin", tags=["admin"])

# 심사 권한자만 감사 로그를 본다(운영 기록이라 일반 회원에게 열지 않는다)
_reviewer = require_permission("profile.review")


@audit_log_router.get("/audit-logs", response_model=list[AuditLogResponseSchema])
async def list_audit_logs(
    _actor=Depends(_reviewer),
    use_case: AuditLogLookupUseCase = Depends(get_audit_log_lookup_use_case),
) -> list[AuditLogResponseSchema]:
    results = await use_case.list_recent()
    return [AuditLogResponseSchema.from_result(result) for result in results]
