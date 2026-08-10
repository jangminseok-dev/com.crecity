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

# 토스페이먼츠(§7-3 확정 PG) — 미설정이면 서버는 뜨되 결제만 실패.
# client는 공개 키(프론트 결제창), secret은 서버 전용(승인·취소 API).
TOSS_CLIENT_KEY = _secrets.get("TOSS_CLIENT_KEY")
TOSS_SECRET_KEY = _secrets.get("TOSS_SECRET_KEY")

# 주문 수수료율(%) — 하드코딩 금지, 주문 생성 시점에 스냅샷된다(BOUNDARIES §7-4).
# 초기값 브랜드 10 / 크리에이터 10 — 런칭 전 경쟁사 실사 후 재조정 전제.
ORDER_BRAND_FEE_PERCENT = int(_secrets.get("ORDER_BRAND_FEE_PERCENT", "10"))
ORDER_CREATOR_FEE_PERCENT = int(_secrets.get("ORDER_CREATOR_FEE_PERCENT", "10"))

# 응답 마감(시간) — 수락 대기·검토 공통 72h(collabstr §3.8), 만료는 주기 스캔이 전이.
ORDER_RESPONSE_DEADLINE_HOURS = int(_secrets.get("ORDER_RESPONSE_DEADLINE_HOURS", "72"))
