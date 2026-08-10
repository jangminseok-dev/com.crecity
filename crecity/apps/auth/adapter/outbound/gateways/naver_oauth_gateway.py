from urllib.parse import urlencode

import httpx

from auth.app.dtos.social_login_dto import SocialProfile
from auth.app.exceptions import OAuthExchangeError
from auth.app.ports.output.social_profile_gateway import SocialProfileGateway

_AUTHORIZE_URL = "https://nid.naver.com/oauth2.0/authorize"
_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
_PROFILE_URL = "https://openapi.naver.com/v1/nid/me"


class NaverOAuthGateway(SocialProfileGateway):
    """네이버 로그인 API — 토큰 발급 요청에 state가 필수다."""

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
            "client_secret": self._client_secret,
            "code": code,
            "state": state,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            token_response = await client.post(_TOKEN_URL, data=data)
            if token_response.status_code != 200:
                raise OAuthExchangeError(f"네이버 토큰 교환 실패: {token_response.status_code}")
            token_payload = token_response.json()
            # 네이버는 실패해도 200으로 error 필드를 실어 줄 수 있다
            if "error" in token_payload:
                raise OAuthExchangeError(f"네이버 토큰 교환 실패: {token_payload['error']}")
            access_token = token_payload.get("access_token", "")
            profile_response = await client.get(
                _PROFILE_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
            if profile_response.status_code != 200:
                raise OAuthExchangeError(f"네이버 프로필 조회 실패: {profile_response.status_code}")
        response = profile_response.json().get("response") or {}
        if "id" not in response:
            raise OAuthExchangeError("네이버 프로필 응답에 id가 없습니다.")
        return SocialProfile(
            provider_user_id=str(response["id"]),
            email=response.get("email") or None,
            name=response.get("name") or response.get("nickname") or "",
        )
