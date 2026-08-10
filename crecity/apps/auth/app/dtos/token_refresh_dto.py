from dataclasses import dataclass


@dataclass(frozen=True)
class TokenRefreshCommand:

    refresh_token: str


@dataclass(frozen=True)
class TokenRefreshResult:

    access_token: str
    refresh_token: str
