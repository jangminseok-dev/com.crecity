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
# 인출 원천징수율(퍼밀) — 사업소득 3.3% = 33‰
WITHDRAWAL_TAX_PERMILLE = int(_secrets.get("WITHDRAWAL_TAX_PERMILLE", "33"))

# 응답 마감(시간) — 수락 대기·검토 공통 72h(collabstr §3.8), 만료는 주기 스캔이 전이.
ORDER_RESPONSE_DEADLINE_HOURS = int(_secrets.get("ORDER_RESPONSE_DEADLINE_HOURS", "72"))
# 마감 임박 알림을 보내는 시점(갭 #76) — 남은 시간이 이 값 이하로 떨어지면 한 번 알린다.
# 무응답 만료는 랭킹 페널티로 이어지므로 지나기 전에 손 쓸 틈을 준다.
ORDER_DEADLINE_WARNING_HOURS = int(_secrets.get("ORDER_DEADLINE_WARNING_HOURS", "12"))
# 인기 랭킹에서 수락 만료 1건이 상쇄하는 성사 주문 수(§3.8 — 무응답 페널티)
RANKING_ACCEPT_EXPIRY_PENALTY = int(_secrets.get("RANKING_ACCEPT_EXPIRY_PENALTY", "2"))
# "빠른 응답" 배지 기준(갭 #80) — 평균 수락 소요가 이 시간 이하 + 표본 최소 건수 + 만료 0건.
# 24h = 응답 마감(72h)의 1/3 — 실거래 분포 확보 후 재조정 전제(launch-checklist §3).
ORDER_FAST_RESPONSE_HOURS = int(_secrets.get("ORDER_FAST_RESPONSE_HOURS", "24"))
ORDER_FAST_RESPONSE_MIN_SAMPLES = int(_secrets.get("ORDER_FAST_RESPONSE_MIN_SAMPLES", "3"))

# 프로필 심사 정량 기준(갭 #16) — 자동 체크의 참고선일 뿐 자동 승인·반려는 하지 않는다.
# 팔로워 1,000(나노 인플루언서 진입선) · 참여율 1.0%(=10‰, 통상 양호 하한).
VETTING_MIN_FOLLOWERS = int(_secrets.get("VETTING_MIN_FOLLOWERS", "1000"))
VETTING_MIN_ENGAGEMENT_PERMILLE = int(_secrets.get("VETTING_MIN_ENGAGEMENT_PERMILLE", "10"))

# 업로드 파일 저장 루트 — 로컬 디스크 시작(오브젝트 스토리지 전환 시 어댑터 교체).
UPLOAD_DIR = _secrets.get("UPLOAD_DIR", "uploads")
