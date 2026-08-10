from dataclasses import dataclass


@dataclass(frozen=True)
class VerifiedUser:
    """검증된 액세스 토큰의 주인 — 스포크가 '현재 사용자'를 알기 위한 허브 계약.

    account_type은 auth의 AccountType 값 문자열(CREATOR | BRAND) — 허브는
    스포크 enum을 모르므로 문자열로 계약한다.
    roles·permissions는 발급 시점 RBAC 스냅샷 — 인가 검사는 permission 코드가 기준이다.
    """

    id: int
    email: str
    account_type: str
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

    def has_permission(self, code: str) -> bool:
        return code in self.permissions
