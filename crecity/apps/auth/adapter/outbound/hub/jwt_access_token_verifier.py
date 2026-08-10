import jwt

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.app.exceptions import InvalidAccessTokenError
from hub.app.ports.output.access_token_verifier_port import AccessTokenVerifier


class JwtAccessTokenVerifier(AccessTokenVerifier):
    """허브 AccessTokenVerifier 계약의 auth 구현 — 발급(JwtAccessTokenIssuer)과 같은
    HS256 시크릿으로 검증한다. main.py가 허브 조립 지점에 등록한다."""

    def __init__(self, secret: str) -> None:
        self._secret = secret

    def verify(self, token: str) -> VerifiedUser:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise InvalidAccessTokenError("만료된 액세스 토큰입니다.")
        except jwt.InvalidTokenError:
            raise InvalidAccessTokenError("유효하지 않은 액세스 토큰입니다.")
        return VerifiedUser(
            id=int(payload["sub"]),
            email=payload["email"],
            account_type=payload["account_type"],
            # RBAC 도입 전 발급분은 클레임이 없다 — 빈 권한으로 간주(호환)
            roles=tuple(payload.get("roles", ())),
            permissions=tuple(payload.get("permissions", ())),
        )
