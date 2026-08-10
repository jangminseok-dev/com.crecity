from core.key.secret_manager import get_secret_manager

# `.env` 로드·조회는 전역 비밀값 관리자가 전담한다(core/key/secret_manager.py).
_secrets = get_secret_manager()

DATABASE_URL = _secrets.require("DATABASE_URL").replace(
    "postgresql://", "postgresql+psycopg://"
)

# 실행 환경 — 쿠키 Secure 속성 등 환경 분기에 사용.
ENV = _secrets.get("ENV", "development")

# 리프레시 토큰 저장소(auth) — 컨테이너는 redis://redis:6379/0 로 덮어쓴다.
# 로컬 기본 6380: redoceanmap 백엔드 PC 포워딩(6379)과의 충돌 회피.
REDIS_URL = _secrets.get("REDIS_URL", "redis://localhost:6380/0")

# 소셜 로그인(OAuth) 클라이언트 자격 — 미설정이면 서버는 뜨되 해당 제공자 로그인만 실패.
KAKAO_CLIENT_ID = _secrets.get("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = _secrets.get("KAKAO_CLIENT_SECRET")
NAVER_CLIENT_ID = _secrets.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = _secrets.get("NAVER_CLIENT_SECRET")
GOOGLE_CLIENT_ID = _secrets.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _secrets.get("GOOGLE_CLIENT_SECRET")

# 토큰 수명 — 액세스 30분 / 리프레시 14일(회전식 1회용).
AUTH_ACCESS_TOKEN_TTL_SECONDS = int(_secrets.get("AUTH_ACCESS_TOKEN_TTL_SECONDS", "1800"))
AUTH_REFRESH_TOKEN_TTL_SECONDS = int(_secrets.get("AUTH_REFRESH_TOKEN_TTL_SECONDS", "1209600"))
