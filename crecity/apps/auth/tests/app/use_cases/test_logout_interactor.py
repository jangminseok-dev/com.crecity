from auth.app.dtos.logout_dto import LogoutCommand
from auth.app.use_cases.logout_interactor import LogoutInteractor


class _StubRefreshTokenStore:
    def __init__(self, tokens: dict[str, int]):
        self.tokens = tokens

    async def save(self, token, user_id, ttl_seconds):
        raise NotImplementedError

    async def pop(self, token):
        return self.tokens.pop(token, None)


async def test_로그아웃하면_리프레시_토큰이_폐기된다():
    store = _StubRefreshTokenStore({"live-token": 1})
    await LogoutInteractor(refresh_tokens=store).logout(LogoutCommand(refresh_token="live-token"))
    assert store.tokens == {}  # 저장소에서 사라져 재사용 불가


async def test_이미_없는_토큰이어도_멱등하게_성공한다():
    store = _StubRefreshTokenStore({})
    # 예외 없이 통과해야 한다 — 회전·만료된 토큰의 로그아웃도 정상 흐름
    await LogoutInteractor(refresh_tokens=store).logout(LogoutCommand(refresh_token="gone"))
