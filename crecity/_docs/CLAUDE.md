# CLAUDE.md — 백엔드 (crecity)

공통 원칙 → [[CLAUDE|CLAUDE (루트)]] · 요구사항 정본 → [[_docs/collabstr-analysis|collabstr 분석]]
· 앱 경계·트랜잭션 경계 → [[crecity/_docs/BOUNDARIES|BOUNDARIES]]

Python / FastAPI 백엔드. 앱 **내부**는 헥사고날/클린 아키텍처(`adapter → app → domain`),
앱 **사이**는 스타 토폴로지(허브-스포크)를 따른다. 두 구조는 `crecity/.importlinter`로 강제된다.

---

## 라우터 컨벤션 — 실기능 자기소개 + 프랙탈 (필수)

새 라우터를 만들 때는 반드시 다음을 함께 만든다:

1. **`GET <prefix>/myself` 자기소개 엔드포인트** — 배역/은유가 아니라 **실제 기능**을 설명한다
   (제공 엔드포인트·데이터·제약을 명시).
2. **프랙탈 단면** — 자기소개도 전체 헥사고날 단면을 관통한다:
   ```
   adapter/inbound/api/schemas/<이름>_schema.py     # 요청/응답 pydantic 스키마
   app/dtos/<이름>_dto.py                            # Query·Response (frozen dataclass)
   app/ports/input/<이름>_use_case.py                # UseCase ABC
   app/ports/output/<이름>_record_port.py            # 활동 기록 아웃바운드 포트
   app/use_cases/<이름>_interactor.py                # 대장 — record 포트를 실제 사용
   adapter/outbound/log_<이름>_record_adapter.py     # 임시 로그 구현 (영속 필요 시 PG 교체)
   dependencies/<이름>_provider.py                   # DI 프로바이더
   tests/app/use_cases/test_<이름>_interactor.py     # 스텁 포트로 검증
   ```
3. **유스케이스는 어댑터 스키마가 아니라 app DTO를 받는다** (계층 계약 — 스키마↔DTO 변환은 라우터 몫).
4. 아웃바운드 포트는 빈 껍데기 금지 — 인터랙터가 실제 호출하는 형태로 만든다.

## 수직 슬라이스 1:1 컨벤션 (필수)

새 앱·새 기능(슬라이스)을 만들 때 **슬라이스(유스케이스)당 각 계층 파일 1개**:
`<이름>_router` · `<이름>_schema` · `<이름>_dto` · `ports/input/<이름>_use_case` ·
`ports/output/<이름>_*_port` · `<이름>_interactor` · `<이름>_provider` · `test_<이름>_interactor`.
hub도 동일하다.

- 기계적 파일명 일치가 아니라 "계층마다 담당 파일 1개"가 기준. 허용 예외:
  ① HTTP 표면 없는 슬라이스는 schema/router 생략(스켈레톤 금지)
  ② DTO·리포지토리는 도메인어 명명 가능 ③ entity/VO/mapper는 로직 있을 때만.
- 한 파일에 여러 슬라이스 금지: 라우터·스키마·프로바이더·테스트 잡탕 금지.
- 검증 루틴: 라우트 표 전후 diff + `pytest apps` + `lint-imports`.

---

## 스타 토폴로지 — 앱 사이 구조 (허브-스포크)

- **허브 = `apps/hub`** — 앱 간 협력의 단일 교차점. 계약(포트+DTO)만 소유.
- **스포크 = `hub`를 제외한 `apps/` 전부** — 허브가 공개한 추상에만 의존하는 독립 도메인 노드.

| 방향 | 허용 | 이유 |
|------|------|------|
| 스포크 → 허브 | ✅ | 스포크는 허브 포트/DTO에만 의존 |
| 스포크 → 스포크 | ⛔ | 직접 import·순환 금지. 교차 협력은 허브 경유 |
| 허브 → 스포크 | ⛔ | 허브가 특정 스포크를 알면 스타가 메시로 무너짐 |

`core/`는 순수 인프라 공유(DB 세션·`Base`·config)만 담당하며 도메인 협력은 허브가 맡는다.

## 앱 지도

| 앱 | 유형 | 담당 | 문서 |
| --- | --- | --- | --- |
| hub | 허브 | 교차 협력 계약(포트·DTO) 소유 | [[crecity/apps/hub/_docs/CLAUDE\|hub CLAUDE]] |
| auth | 스포크 | 회원 인증 · 크리에이터/브랜드 계정 경계 | [[crecity/apps/auth/_docs/CLAUDE\|auth CLAUDE]] |
| creator | 스포크 | 크리에이터 프로필 · 판매 패키지 | [[crecity/apps/creator/_docs/CLAUDE\|creator CLAUDE]] |
| order | 스포크 | 주문 상태머신 · 에스크로/잔액 원장 | [[crecity/apps/order/_docs/CLAUDE\|order CLAUDE]] |

새 앱은 `crecity/apps/<app>/_docs/CLAUDE.md` + 심볼릭 링크 `<app>/CLAUDE.md → _docs/CLAUDE.md`를
추가하고 위 표에 한 줄 등록한다. 후속 앱의 경계·소유 데이터·착수 순서는
[[crecity/_docs/BOUNDARIES|BOUNDARIES]]가 정본이다.

## 트랜잭션 경계 원칙 (필수 — 상세는 BOUNDARIES §1·§3)

- **원자성이 필수인 상태 변경은 같은 스포크(=같은 DB 트랜잭션)에 둔다.** 교차 스포크 보상
  로직이 필요해 보이면 경계를 잘못 그은 것이다. Saga·인메모리 이벤트 버스는 도입하지 않는다.
- 결과적 정합성으로 충분한 부수효과(알림 등)만 허브 이벤트로 뺀다 — 유실 불허 시 Outbox
  (첫 소비자인 notification 앱과 함께 도입, 선제 구축 금지).
- 외부 API(PG·이체·알림톡)는 원자적일 수 없다 — 상태 기록+재시도로 다루고 전용 스포크에 격리한다.
- 단순 조회라도 어댑터에서 리포지토리 직접 접근 금지(CQRS 우회 기각 — 2026-08-10 확정).
  유스케이스 계층을 항상 관통한다.

---

## 앱 내부 레이어 (헥사고날)

```
<app>/
├── domain/{entities,value_objects}/   # 순수 도메인 — 외부 의존 금지
├── app/
│   ├── ports/{input,output}/          # UseCase / Repository ABC
│   ├── use_cases/                     # Interactor (대장)
│   └── dtos/                          # 레이어 간 전달 객체
├── adapter/
│   ├── inbound/api/{schemas,v1}/      # Pydantic 스키마 · FastAPI 라우터
│   └── outbound/                      # 포트 구현체 (log/pg/orm/mappers/gateways)
├── dependencies/                      # FastAPI DI 프로바이더
└── tests/
```

**의존 방향:** `adapter → app → domain` (역방향 금지). 어댑터 스키마를 app에서 직접 import하면
계층 역전 — 필요하면 `app/dtos` 또는 `TYPE_CHECKING` 가드를 쓴다.

## 임포트 / 세션 규칙

- 앱은 최상위 패키지로 인식된다(`from creator.app.ports... import ...`). `main.py`가
  `sys.path`에 `apps/`를 등록하고, lint/스크립트는 `PYTHONPATH=apps`로 맞춘다.
- 세션·베이스: `from core.database import get_db, Base`.
- **비밀값·환경 변수는 `core/key/secret_manager.py`로 수렴한다.**

## DB 스키마 규칙 — 3NF 기본 (필수)

새 테이블·컬럼은 **3NF를 기본으로 설계한다** (2026-08-10 확정):

- 다중값을 한 컬럼에 넣지 않는다(CSV·JSON 배열 금지 — 조인 테이블로).
- 비키 속성 간 이행적 종속 금지 — 다른 테이블이 소유한 속성을 복사 저장하지 않는다
  (예: 패키지에 프로필 name 중복 저장 금지, FK로 참조).
- 참조 대상에 딸린 속성이 생기면(카테고리 설명 등) 그 시점에 별도 테이블로 분리한다.
- **허용 예외는 명시적 확정 결정뿐**: 주문 시점 수수료율 스냅샷(BOUNDARIES §7-4) 같은
  이력 보존 목적 복사. 새 예외는 사용자 승인 없이 만들지 않는다.

## 비밀값 규칙 — `.env` 로드는 한 곳에서만 (필수)

`load_dotenv`를 직접 부르는 곳은 `core/key/secret_manager.py` **하나뿐이다**.

| 쓰는 쪽 | 방법 |
|---|---|
| 앱 런타임(어댑터·프로바이더·유스케이스) | `from core.config import ...` — 상수만 소비 |
| 스크립트 · 마이그레이션 · 엔트리포인트 | `get_secret_manager().get(name, default)` / `.require(name)` |
| 새 설정값 추가 | `.env.example`에 키 등록 → `core/config.py`에 상수 한 줄 |

## async def vs def

I/O-bound(DB·HTTP)는 `async def`, CPU-bound(수치·변환)는 `def`. 포트(ABC)와 구현체의
`def`/`async def`를 일치시킨다. 무거운 CPU 작업은 호출 측에서 `asyncio.to_thread`로 분리한다.
