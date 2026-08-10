from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorizeUrlQuery:

    provider: str
    redirect_uri: str
    state: str


@dataclass(frozen=True)
class AuthorizeUrlResult:

    authorize_url: str


@dataclass(frozen=True)
class SocialLoginCommand:

    provider: str
    code: str
    redirect_uri: str
    state: str
    account_type: str  # 신규 가입 시에만 사용 — 기존 계정은 저장된 유형 유지


@dataclass(frozen=True)
class SocialProfile:
    """게이트웨이가 제공자 API에서 가져온 프로필 (아웃바운드 포트 반환형)."""

    provider_user_id: str
    email: str | None  # 동의 미체크 시 None — 로그인은 이메일 필수
    name: str


@dataclass(frozen=True)
class AuthenticatedUser:

    id: int
    email: str
    name: str
    account_type: str


@dataclass(frozen=True)
class SocialLoginResult:

    access_token: str
    refresh_token: str
    user: AuthenticatedUser
    is_new_user: bool
