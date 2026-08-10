from core.key.secret_manager import get_secret_manager

# `.env` 로드·조회는 전역 비밀값 관리자가 전담한다(core/key/secret_manager.py).
_secrets = get_secret_manager()

DATABASE_URL = _secrets.require("DATABASE_URL").replace(
    "postgresql://", "postgresql+psycopg://"
)

# 실행 환경 — 쿠키 Secure 속성 등 환경 분기에 사용.
ENV = _secrets.get("ENV", "development")

# 리프레시 토큰 저장소(auth 예정) — 컨테이너는 redis://redis:6379/0 로 덮어쓴다.
# 로컬 기본 6380: redoceanmap 백엔드 PC 포워딩(6379)과의 충돌 회피.
REDIS_URL = _secrets.get("REDIS_URL", "redis://localhost:6380/0")
