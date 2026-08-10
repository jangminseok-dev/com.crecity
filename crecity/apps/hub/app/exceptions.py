class InvalidAccessTokenError(Exception):
    """무효·만료·위조된 액세스 토큰 — 소비 측에서 401로 변환."""
