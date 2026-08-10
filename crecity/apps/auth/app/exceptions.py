class UnsupportedProviderError(Exception):
    """지원하지 않는 OAuth 제공자 — 라우터에서 404로 변환."""


class EmailNotProvidedError(Exception):
    """제공자가 이메일을 주지 않음(동의 미체크 등) — 라우터에서 400으로 변환."""


class OAuthExchangeError(Exception):
    """제공자와의 코드 교환·프로필 조회 실패 — 라우터에서 502로 변환."""


class InvalidRefreshTokenError(Exception):
    """무효·만료·재사용된 리프레시 토큰 — 라우터에서 401로 변환."""
