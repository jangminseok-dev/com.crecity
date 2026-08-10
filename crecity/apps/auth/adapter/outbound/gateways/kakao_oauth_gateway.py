from urllib.parse import urlencode

import httpx

from auth.app.dtos.social_login_dto import SocialProfile
from auth.app.exceptions import OAuthExchangeError
from auth.app.ports.output.social_profile_gateway import SocialProfileGateway

_AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
_PROFILE_URL = "https://kapi.kakao.com/v2/user/me"


class KakaoOAuthGateway(SocialProfileGateway):
    """카카오 로그인 REST API — 이메일은 '카카오 로그인 동의항목'에서 account_email
    활성화가 전제다(미동의 시 email이 비어 온다)."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    async def fetch_profile(self, code: str, redirect_uri: str, state: str) -> SocialProfile:
        data = {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        if self._client_secret:
            data["client_secret"] = self._client_secret
        async with httpx.AsyncClient(timeout=10) as client:
            token_response = await client.post(_TOKEN_URL, data=data)
            if token_response.status_code != 200:
                raise OAuthExchangeError(f"카카오 토큰 교환 실패: {token_response.status_code}")
            access_token = token_response.json().get("access_token", "")
            profile_response = await client.get(
                _PROFILE_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
            if profile_response.status_code != 200:
                raise OAuthExchangeError(f"카카오 프로필 조회 실패: {profile_response.status_code}")
        payload = profile_response.json()
        kakao_account = payload.get("kakao_account") or {}
        profile = kakao_account.get("profile") or {}
        return SocialProfile(
            provider_user_id=str(payload["id"]),
            email=kakao_account.get("email") or None,
            name=profile.get("nickname") or "",
        )
