from urllib.parse import urlencode

import httpx

from auth.app.dtos.social_login_dto import SocialProfile
from auth.app.exceptions import OAuthExchangeError
from auth.app.ports.output.social_profile_gateway import SocialProfileGateway

_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_PROFILE_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleOAuthGateway(SocialProfileGateway):
    """구글 OAuth 2.0(OpenID Connect) — scope는 openid·email·profile 고정."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid email profile",
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    async def fetch_profile(self, code: str, redirect_uri: str, state: str) -> SocialProfile:
        data = {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            token_response = await client.post(_TOKEN_URL, data=data)
            if token_response.status_code != 200:
                raise OAuthExchangeError(f"구글 토큰 교환 실패: {token_response.status_code}")
            access_token = token_response.json().get("access_token", "")
            profile_response = await client.get(
                _PROFILE_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
            if profile_response.status_code != 200:
                raise OAuthExchangeError(f"구글 프로필 조회 실패: {profile_response.status_code}")
        payload = profile_response.json()
        if "sub" not in payload:
            raise OAuthExchangeError("구글 프로필 응답에 sub가 없습니다.")
        return SocialProfile(
            provider_user_id=str(payload["sub"]),
            email=payload.get("email") or None,
            name=payload.get("name") or "",
        )
