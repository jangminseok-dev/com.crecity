#!/usr/bin/env python3
"""페르소나 여정 회귀 — 방문자 10명이 회원가입부터 목적 달성까지 실제 서버를 관통한다.

smoke.py는 엔드포인트 하나씩을, e2e.py는 화면 렌더를 본다. 이 스크립트는 **한 사람의 여정**을
본다 — 가입 → 프로필/탐색 → 주문 → 납품 → 정산까지 상태머신이 순서대로 넘어가는지,
원장 금액이 여정 끝에 맞아떨어지는지.

외부 접점 두 곳만 스텁으로 바꾼 백엔드를 :8001에 따로 띄운다(헥사고날 포트 경계 그대로):
  · 카카오 OAuth 프로필 조회 — 인가 코드 대신 "이메일|이름|uid" 문자열을 프로필로 돌려준다
  · 토스페이먼츠 승인/취소 — 항상 성공
회원가입·토큰 발급·주문·원장·알림은 전부 실제 코드·실제 DB(5433)·실제 Redis(6380)를 탄다.

실행:
    .venv/bin/python scripts/personas.py              # API 여정만
    .venv/bin/python scripts/personas.py --browser    # 여정 끝의 화면까지 (프론트 :3000 필요)
    .venv/bin/python scripts/personas.py --only 2,6   # 특정 페르소나만 (의존 페르소나는 자동 포함)
    .venv/bin/python scripts/personas.py --cleanup    # 지금까지 만든 페르소나 데이터 전부 삭제

사전 조건: docker compose up -d. (:8000 백엔드는 없어도 되지만 --browser는 프론트가 :8000을 본다)
매 실행마다 고유 접미사로 계정을 만들므로 재실행이 안전하다. 남은 데이터는 --cleanup으로 지운다.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
import time
import traceback
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv/bin/python")
PORT = int(os.environ.get("PERSONA_PORT", "8001"))
BACKEND = f"http://127.0.0.1:{PORT}"
FRONTEND = "http://localhost:3000"
RUN = datetime.now().strftime("%m%d%H%M%S")  # 계정·슬러그 충돌 방지 접미사
YEAR = datetime.now().year

_results: list[tuple[bool, str, str]] = []  # (ok, persona, label)
_notes: list[tuple[str, str]] = []  # (persona, 관찰) — 합격/불합격이 아니라 사람이 판단할 발견
_current = ["?"]

# ─────────────────────────────── 스텁 백엔드 ───────────────────────────────

_SERVER_SNIPPET = r"""
import uvicorn
from auth.app.dtos.social_login_dto import SocialProfile
from auth.app.ports.output.social_profile_gateway import SocialProfileGateway
from payment.app.ports.output.payment_gateway import PaymentGateway
import auth.dependencies.social_login_provider as social_provider
import payment.dependencies.payment_confirmation_provider as payment_provider


class FakeOAuthGateway(SocialProfileGateway):
    # 인가 코드 자리에 "이메일|이름|uid"를 넣으면 그대로 프로필이 된다 — 제공자 교환만 생략
    def __init__(self, client_id, client_secret): ...
    def authorize_url(self, redirect_uri, state): return "http://stub/authorize"
    async def fetch_profile(self, code, redirect_uri, state):
        email, name, uid = code.split("|")
        return SocialProfile(provider_user_id=uid, email=email, name=name)


class FakePgGateway(PaymentGateway):
    def __init__(self, secret_key): ...
    async def confirm(self, payment_key, pg_order_id, amount_krw): return None
    async def cancel(self, payment_key, reason): return None


social_provider.KakaoOAuthGateway = FakeOAuthGateway
payment_provider.TossPaymentsGateway = FakePgGateway

import main
uvicorn.run(main.app, host="127.0.0.1", port=%d, log_level="warning")
"""


def start_stub_backend() -> subprocess.Popen:
    proc = subprocess.Popen(
        [PY, "-c", _SERVER_SNIPPET % PORT],
        cwd=ROOT / "crecity",
        env={"PYTHONPATH": ".:apps", "PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "")},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    for _ in range(60):
        time.sleep(0.5)
        if proc.poll() is not None:
            raise RuntimeError(f"스텁 백엔드가 죽었습니다:\n{proc.stderr.read()[-2000:]}")
        try:
            if httpx.get(f"{BACKEND}/health", timeout=2).status_code == 200:
                return proc
        except httpx.HTTPError:
            continue
    proc.kill()
    raise RuntimeError("스텁 백엔드가 30초 안에 뜨지 않았습니다.")


def run_script(name: str, *args: str) -> str:
    """crecity/scripts/*.py를 실제 환경 그대로 부른다(로직을 두 벌로 만들지 않는다)."""
    result = subprocess.run(
        [PY, f"scripts/{name}", *args],
        cwd=ROOT / "crecity",
        env={"PYTHONPATH": ".:apps", "PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "")},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{name} 실패: {result.stderr.strip()[-500:]}")
    return result.stdout


# ─────────────────────────────── 검사·요청 헬퍼 ───────────────────────────────


class StepFailed(Exception):
    """여정이 더 못 나아가는 실패 — 이후 단계는 건너뛴다."""


def check(ok: bool, label: str, detail: str = "") -> bool:
    _results.append((bool(ok), _current[0], f"{label}{f' — {detail}' if detail else ''}"))
    print(f"    {'✓' if ok else '✗'} {label}{f' — {detail}' if detail and not ok else ''}")
    return bool(ok)


def note(text: str) -> None:
    """설계 판단이 필요한 관찰 — 통과 수에 섞지 않고 말미에 따로 모은다."""
    _notes.append((_current[0], text))
    print(f"    ⓘ {text}")


def must(ok: bool, label: str, detail: str = "") -> None:
    if not check(ok, label, detail):
        raise StepFailed(label)


class Client:
    """페르소나 한 명 = 토큰 하나. 응답을 (상태코드, JSON)으로 돌려준다."""

    def __init__(self, http: httpx.Client, token: str | None = None) -> None:
        self._http = http
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def call(
        self,
        method: str,
        path: str,
        json_body: Any = None,
        files: dict | None = None,
        data: dict | None = None,
        params: dict | None = None,
    ) -> tuple[int, Any]:
        response = self._http.request(
            method,
            f"{BACKEND}{path}",
            json=json_body,
            files=files,
            data=data,
            params=params,
            headers=self._headers(),
            timeout=30,
        )
        try:
            payload = response.json() if response.content else None
        except ValueError:
            payload = None
        return response.status_code, payload

    def ok(self, method: str, path: str, label: str, expect: int = 200, **kw) -> Any:
        """기대 상태코드가 아니면 여정을 멈춘다 — 이후 단계는 의미가 없다."""
        status, payload = self.call(method, path, **kw)
        detail = "" if status == expect else f"기대 {expect} / 실제 {status} {str(payload)[:160]}"
        must(status == expect, label, detail)
        return payload

    def expect(self, method: str, path: str, expect: int, label: str, **kw) -> Any:
        """기대 상태코드를 확인만 하고 계속 간다(거부 경로 검증용)."""
        status, payload = self.call(method, path, **kw)
        check(status == expect, label, f"기대 {expect} / 실제 {status} {str(payload)[:160]}")
        return payload


class Person:
    """가입한 사람 — 이름·역할·토큰·(크리에이터면) 슬러그."""

    def __init__(self, key: str, name: str, account_type: str, http: httpx.Client) -> None:
        self.key = key
        self.name = name
        self.account_type = account_type
        self.email = f"{key}-{RUN}@persona.crecity.local"
        self.uid = f"kakao-{key}-{RUN}"
        self.api = Client(http)
        self.user_id = 0
        self.refresh_token = ""
        self.slug = f"{key}-{RUN}"
        self.package_id = 0

    def login(self, expect_new: bool | None = True) -> dict:
        """카카오 로그인(스텁 프로필) — 신규면 계정이 만들어진다. 실제 발급기 토큰을 받는다."""
        payload = self.api.ok(
            "POST",
            "/auth/social/kakao/login",
            f"{self.name} 카카오 {'회원가입' if expect_new else '로그인'}",
            json_body={
                "code": f"{self.email}|{self.name}|{self.uid}",
                "redirect_uri": f"{FRONTEND}/oauth/kakao/callback",
                "state": "persona",
                "account_type": self.account_type,
            },
        )
        if expect_new is not None:
            check(payload["is_new_user"] is expect_new, "신규 가입 여부", str(payload["is_new_user"]))
        check(payload["user"]["account_type"] == self.account_type, f"계정 유형 {self.account_type}")
        self.api.token = payload["access_token"]
        self.refresh_token = payload["refresh_token"]
        self.user_id = payload["user"]["id"]
        return payload


def png_bytes(width: int = 8, height: int = 8, color: tuple = (200, 120, 160)) -> bytes:
    """표준 라이브러리로 만든 단색 PNG — 포트폴리오·지표 스크린샷·납품 파일용."""
    rows = b"".join(b"\x00" + bytes(color) * width for _ in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


def relay_notifications() -> None:
    run_script("notification_outbox_worker.py")


# ─────────────────────────────── 공통 여정 조각 ───────────────────────────────


def register_creator(p: Person, category: str, tagline: str, location: str) -> dict:
    p.api.expect("GET", "/creator/my/profile", 404, "가입 직후 프로필 없음")
    profile = p.api.ok(
        "POST",
        "/creator/profiles",
        "프로필 등록",
        expect=201,
        json_body={
            "slug": p.slug,
            "name": p.name,
            "tagline": tagline,
            "bio": f"{p.name}입니다. {tagline} 콘텐츠를 만듭니다. 협업 문의 환영합니다.",
            "location": location,
            "primary_category": category,
        },
    )
    check(profile["status"] == "PENDING", "등록 직후 심사 대기(PENDING)", profile["status"])
    return profile


def add_package(p: Person, platform: str, title: str, price: int, revision_limit: int = 2) -> int:
    package = p.api.ok(
        "POST",
        f"/creator/profiles/{p.slug}/packages",
        f"패키지 등록 '{title}' {price:,}원",
        expect=201,
        json_body={
            "platform": platform,
            "title": title,
            "description": "피드 1건 + 스토리 1건, 원본 파일 제공",
            "price_krw": price,
            "revision_limit": revision_limit,
            "usage_rights": "브랜드 채널 2차 활용 3개월",
        },
    )
    p.package_id = package["id"]
    return package["id"]


def approve_profile(admin: Person, p: Person) -> dict:
    pending = admin.api.ok("GET", "/admin/profiles/pending", "운영자 심사 대기 목록")
    row = next((r for r in pending if r["slug"] == p.slug), None)
    must(row is not None, f"심사 대기 목록에 {p.name} 포함")
    result = admin.api.ok("POST", f"/admin/profiles/{row['id']}/approve", f"운영자 승인 → {p.name}")
    check(result["status"] == "APPROVED", "승인 상태 APPROVED", result["status"])
    return row


def pay(brand: Person, checkout: dict, label: str) -> dict:
    """체크아웃 결과로 승인까지 — PG 청구액이 0이면(전액 크레딧) payment_key 없이."""
    pg_amount = checkout["pg_amount_krw"]
    confirmed = brand.api.ok(
        "POST",
        "/payment/confirm",
        f"{label} 결제 승인 (PG {pg_amount:,}원 · 크레딧 {checkout['credit_applied_krw']:,}원)",
        json_body={
            "payment_key": f"stub-{RUN}" if pg_amount > 0 else "",
            "pg_order_id": checkout["pg_order_id"],
            "amount_krw": pg_amount,
        },
    )
    return confirmed


def order_package(brand: Person, package_id: int, label: str, requirements: str = "제품 소개 피드 1건 부탁드립니다.") -> dict:
    checkout = brand.api.ok(
        "POST", "/payment/checkouts", f"{label} 체크아웃", expect=201,
        json_body={"package_id": package_id, "requirements": requirements},
    )
    confirmed = pay(brand, checkout, label)
    order = brand.api.ok("GET", f"/order/orders/{confirmed['order_id']}", "주문 조회")
    check(order["status"] == "PENDING_ACCEPT", "주문 상태 PENDING_ACCEPT", order["status"])
    check(order["brand_total_krw"] == checkout["amount_krw"], "체크아웃 금액 == 주문 브랜드 총액")
    return order


def deliver_and_submit(creator: Person, order_id: int, url: str = "https://www.instagram.com/p/persona-post/") -> dict:
    creator.api.ok(
        "POST", f"/order/orders/{order_id}/deliverables/links", "납품 링크 등록", expect=201,
        json_body={"url": url, "caption": "게시 완료했습니다. #광고 표기 포함"},
    )
    order = creator.api.ok("POST", f"/order/orders/{order_id}/submit", "결과물 제출")
    check(order["status"] == "IN_REVIEW", "제출 후 IN_REVIEW", order["status"])
    return order


def complete_order(brand: Person, creator: Person, order_id: int) -> dict:
    """수락 → 링크 납품 → 제출 → 승인 — 가장 짧은 완주 경로."""
    accepted = creator.api.ok("POST", f"/order/orders/{order_id}/accept", "크리에이터 수락")
    check(accepted["status"] == "IN_PROGRESS", "수락 후 IN_PROGRESS", accepted["status"])
    deliver_and_submit(creator, order_id)
    done = brand.api.ok("POST", f"/order/orders/{order_id}/approve", "브랜드 구매 확정")
    check(done["status"] == "COMPLETED", "확정 후 COMPLETED", done["status"])
    return done


def balance(p: Person) -> int:
    return p.api.ok("GET", "/order/balance", f"{p.name} 잔액 조회")["balance_krw"]


# ─────────────────────────────── 페르소나 여정 ───────────────────────────────


def journey_admin(w: World) -> None:
    """운영자 김운영 — 방문자는 아니지만 심사·정산·분쟁 판정을 맡는 조연. 가입 플로우가 없어
    일반 계정으로 가입한 뒤 auth_grant_role.py로 역할을 받는다(실제 운영 절차와 동일)."""
    admin = w.person("admin", "김운영", "CREATOR")
    admin.login()
    admin.api.expect("GET", "/admin/profiles/pending", 403, "역할 부여 전 운영 API 차단")
    run_script("auth_grant_role.py", admin.email, "admin")
    admin.login(expect_new=False)  # 역할이 실린 토큰을 다시 받는다
    admin.api.ok("GET", "/admin/dashboard/metrics", "역할 부여 후 운영 지표 접근")


def journey_1_seoyeon(w: World) -> None:
    """① 박서연 (27, 뷰티 크리에이터, 팔로워 1.2만) — "내 프로필을 마켓에 올려 브랜드 눈에 띄고 싶다"
    가입 → 프로필·패키지·포트폴리오·FAQ·채널 지표 등록 → 심사 통과 → 목록 노출 → 조회수 확인"""
    p = w.person("seoyeon", "박서연", "CREATOR")
    p.login()
    register_creator(p, "뷰티", "데일리 메이크업 · 스킨케어 리뷰", "서울")
    add_package(p, "INSTAGRAM", "인스타 피드 1건 + 스토리", 150_000)
    add_package(p, "YOUTUBE", "유튜브 쇼츠 리뷰 1건", 300_000)
    packages = p.api.ok("GET", f"/creator/profiles/{p.slug}/packages", "내 패키지 목록")
    check(len(packages) == 2, "패키지 2개", str(len(packages)))
    p.package_id = packages[0]["id"]

    item = p.api.ok(
        "POST", "/creator/my/portfolio", "포트폴리오 사진 업로드", expect=201,
        files={"file": ("look.png", png_bytes(), "image/png")},
    )
    check(bool(item.get("image_url")), "업로드된 사진 URL 발급")
    p.api.ok(
        "POST", "/creator/my/faqs", "FAQ 등록", expect=201,
        json_body={"question": "제품 협찬만도 가능한가요?", "answer": "패키지 금액 기준으로만 진행합니다."},
    )
    analytics = p.api.ok(
        "POST", "/creator/my/analytics", "인스타그램 채널 지표 제출", expect=201,
        files={"file": ("insight.png", png_bytes(color=(90, 90, 200)), "image/png")},
        data={"platform": "INSTAGRAM", "followers_count": "12000", "engagement_permille": "45",
              "avg_views": "8000", "top_audience_region": "서울"},
    )
    check(analytics["followers_count"] == 12000, "지표 저장 확인")

    listing = p.api.ok("GET", "/creator/profiles", "심사 전 마켓 목록", params={"q": p.name})
    check(all(i["slug"] != p.slug for i in listing["items"]), "심사 전에는 목록에 안 보임")

    row = approve_profile(w.admin, p)
    check(row["vetting_passed"] is True, "검증 기준(팔로워 1천·참여율 1%) 통과 표시", str(row.get("vetting_passed")))

    listing = p.api.ok("GET", "/creator/profiles", "승인 후 마켓 목록", params={"q": p.name})
    check(any(i["slug"] == p.slug for i in listing["items"]), "승인 후 목록에 노출")
    listed = next((i for i in listing["items"] if i["slug"] == p.slug), {})
    check(listed.get("price_from") == 150_000, "목록 최저가 = 15만원", str(listed.get("price_from")))
    check(bool(listed.get("cover_image_url")), "목록 커버 = 포트폴리오 사진")

    guest = Client(w.http)
    public = guest.ok("GET", f"/creator/profiles/{p.slug}", "비로그인 방문자가 공개 프로필 조회")
    check(public["followers_total"] == 12000, "공개 프로필 팔로워 합계", str(public["followers_total"]))
    guest.ok("POST", f"/creator/profiles/{p.slug}/views", "방문 기록", expect=204)
    views = p.api.ok("GET", "/creator/my/profile/views", "내 조회수 추이")
    check(views["total"] >= 1, "조회수 1 이상 집계", str(views["total"]))
    mine = p.api.ok("GET", "/creator/my/profile", "내 프로필")
    check(mine["status"] == "APPROVED" and mine["accepting_orders"] is True, "승인·주문 수신 상태")


def journey_2_junho(w: World) -> None:
    """② 이준호 (34, 소규모 D2C 스킨케어 대표) — "처음 인플루언서 마케팅, 한 건 안전하게 끝내고 싶다"
    브랜드 가입 → 카테고리·가격 탐색 → 주문·결제(에스크로) → 납품 승인 → 리뷰 → 수수료 대조"""
    b = w.person("junho", "이준호", "BRAND")
    b.login()
    s = w.people["seoyeon"]
    guest = Client(w.http)
    guest.ok("GET", "/order/fee-policy", "수수료 정책 확인(비로그인)")
    listing = b.api.ok("GET", "/creator/profiles", "뷰티 카테고리 · 낮은 가격순 탐색",
                       params={"category": "뷰티", "sort": "price_asc"})
    check(any(i["slug"] == s.slug for i in listing["items"]), "탐색 결과에 박서연 포함")
    b.api.ok("GET", f"/creator/profiles/{s.slug}/portfolio", "포트폴리오 보기")
    b.api.ok("GET", f"/creator/profiles/{s.slug}/faqs", "FAQ 보기")
    b.api.ok("GET", f"/creator/profiles/{s.slug}/similar", "비슷한 크리에이터 추천")
    packages = b.api.ok("GET", f"/creator/profiles/{s.slug}/packages", "패키지 보기")
    pkg = min(packages, key=lambda x: x["price_krw"])

    order = order_package(b, pkg["id"], "인스타 피드 주문")
    fee = b.api.ok("GET", "/order/fee-policy", "수수료율")
    expected_total = pkg["price_krw"] + pkg["price_krw"] * fee["brand_fee_percent"] // 100
    expected_payout = pkg["price_krw"] - pkg["price_krw"] * fee["creator_fee_percent"] // 100
    check(order["brand_total_krw"] == expected_total, "브랜드 결제액 = 패키지가 + 브랜드 수수료", f"{order['brand_total_krw']:,}")
    check(order["creator_payout_krw"] == expected_payout, "크리에이터 정산액 = 패키지가 − 크리에이터 수수료")
    check(order["counterpart_name"] == s.name, "주문 상대 이름 표시")

    mine = s.api.ok("GET", "/order/orders", "박서연: 받은 주문 목록")
    check(any(o["id"] == order["id"] for o in mine), "박서연 주문함에 도착")
    before = balance(s)
    complete_order(b, s, order["id"])
    check(balance(s) - before == expected_payout, "완료 후 박서연 적립 = 정산액")

    review = b.api.ok(
        "POST", f"/review/orders/{order['id']}/review", "3축 리뷰 작성", expect=201,
        json_body={"communication_score": 5, "timeliness_score": 4, "satisfaction_score": 5,
                   "comment": "소통이 빠르고 결과물 퀄리티가 좋았어요. 다음에도 함께하고 싶습니다."},
    )
    b.api.expect("POST", f"/review/orders/{order['id']}/review", 409, "같은 주문 중복 리뷰 차단",
                 json_body={"communication_score": 1, "timeliness_score": 1, "satisfaction_score": 1, "comment": "중복"})
    s.api.ok("POST", f"/review/reviews/{review['id']}/reply", "박서연 답글", expect=201,
             json_body={"reply": "감사합니다! 다음 시즌 제품도 기대할게요."})
    public = guest.ok("GET", f"/review/creators/{s.slug}", "비로그인 리뷰 목록")
    check(public["total"] == 1 and public["items"][0]["is_locked"] and public["items"][0]["comment"] is None,
          "비로그인은 점수만 보고 본문은 잠김(블러 정책)")
    visible = b.api.ok("GET", f"/review/creators/{s.slug}", "거래한 브랜드의 리뷰 목록")
    check(visible["items"][0]["comment"] and visible["items"][0]["reply"], "거래 당사자는 본문·답글 열람")
    s.api.ok("POST", f"/review/orders/{order['id']}/brand-review", "박서연 → 브랜드 평가", expect=201,
             json_body={"score": 5, "comment": "요구사항이 명확해서 작업이 수월했습니다."})
    rating = guest.ok("GET", f"/review/brands/{b.user_id}/rating", "브랜드 평판 조회")
    check(rating["total"] == 1 and rating["average_score"] == 5, "브랜드 평판 5.0 (1건)")
    report = b.api.ok("GET", f"/order/reports/{YEAR}", "월별 지출 리포트")
    check(any(r["total_krw"] > 0 for r in report), "리포트에 지출 반영")
    w.orders["junho"] = order


def journey_3_minji(w: World) -> None:
    """③ 최민지 (31, 테크 유튜버, 전업) — "초안 컨펌 받고 확실히 정산받아 통장에 넣고 싶다"
    가입·승인 → 주문 수락 → 초안 제출 → 수정 요청 → 재제출·컨펌 → 게시 → 정산 → 인출 → 지급 명세"""
    p = w.person("minji", "최민지", "CREATOR")
    p.login()
    register_creator(p, "테크", "가젯 언박싱 · 앱 리뷰", "판교")
    add_package(p, "YOUTUBE", "유튜브 리뷰 영상 1편", 500_000, revision_limit=2)
    approve_profile(w.admin, p)

    b = w.people["junho"]
    order = order_package(b, p.package_id, "이준호 → 최민지 리뷰 영상 주문")
    p.api.ok("POST", f"/order/orders/{order['id']}/accept", "수락")
    p.api.expect("POST", f"/order/orders/{order['id']}/submit-draft", 409, "납품물 없이 초안 제출 차단")
    p.api.ok("POST", f"/order/orders/{order['id']}/deliverables/links", "초안 링크 등록", expect=201,
             json_body={"url": "https://drive.example.com/draft-v1", "caption": "초안 v1 (비공개 링크)"})
    draft = p.api.ok("POST", f"/order/orders/{order['id']}/submit-draft", "초안 제출")
    check(draft["status"] == "DRAFT_REVIEW", "초안 검토 대기 DRAFT_REVIEW", draft["status"])
    revised = b.api.ok("POST", f"/order/orders/{order['id']}/request-revision", "브랜드 초안 수정 요청",
                       json_body={"comment": "인트로에 브랜드 로고를 3초 이상 노출해 주세요."})
    check(revised["status"] == "IN_PROGRESS" and revised["revisions_used"] == 1, "수정 요청 후 작업 복귀 · 수정 1회 사용")
    revisions = p.api.ok("GET", f"/order/orders/{order['id']}/revisions", "수정 요청 내역")
    check(len(revisions) == 1 and "로고" in revisions[0]["comment"], "수정 요청 코멘트 보존")
    p.api.ok("POST", f"/order/orders/{order['id']}/submit-draft", "수정 초안 재제출")
    approved = b.api.ok("POST", f"/order/orders/{order['id']}/approve-draft", "브랜드 초안 컨펌")
    check(approved["draft_approved"] is True and approved["status"] == "IN_PROGRESS", "컨펌 후 게시 작업 단계")
    p.api.ok(
        "POST", f"/order/orders/{order['id']}/deliverables/files", "최종 영상 썸네일 파일 납품", expect=201,
        files={"file": ("thumb.png", png_bytes(color=(30, 30, 30)), "image/png")},
    )
    deliver_and_submit(p, order["id"], "https://youtu.be/persona-review")
    deliverables = b.api.ok("GET", f"/order/orders/{order['id']}/deliverables", "브랜드: 납품물 목록")
    check(len(deliverables) == 3, "납품물 초안 링크 1 + 파일 1 + 최종 링크 1", str(len(deliverables)))
    done = b.api.ok("POST", f"/order/orders/{order['id']}/approve", "구매 확정")
    check(done["status"] == "COMPLETED", "COMPLETED", done["status"])

    amount = balance(p)
    check(amount == done["creator_payout_krw"], "잔액 = 정산액", f"{amount:,}")
    p.api.expect("POST", "/order/withdrawals", 409, "잔액 초과 인출 거부",
                 json_body={"amount_krw": amount + 1, "bank_name": "카카오뱅크", "account_number": "3333-01-1234567", "account_holder": p.name})
    wd = p.api.ok("POST", "/order/withdrawals", "전액 인출 요청", expect=201,
                  json_body={"amount_krw": amount, "bank_name": "카카오뱅크", "account_number": "3333-01-1234567", "account_holder": p.name})
    fee = p.api.ok("GET", "/order/fee-policy", "세율")
    check(wd["tax_krw"] == amount * fee["withdrawal_tax_permille"] // 1000, "원천세 3.3% 계산", f"{wd['tax_krw']:,}")
    check(wd["payout_krw"] == amount - wd["tax_krw"], "실지급액 = 인출액 − 세금")
    check(balance(p) == 0, "인출 요청 즉시 잔액 0 (이중 인출 방지)")
    pending = w.admin.api.ok("GET", "/admin/withdrawals/pending", "운영자 인출 대기 목록")
    check(any(x["id"] == wd["id"] for x in pending), "대기 목록에 포함")
    settled = w.admin.api.ok("POST", f"/admin/withdrawals/{wd['id']}/complete", "운영자 지급 완료 처리")
    check(settled["status"] == "PAID", "인출 PAID", settled["status"])
    statement = p.api.ok("GET", f"/order/withdrawals/statements/{YEAR}", "연간 지급 명세")
    check(statement["count"] >= 1 and statement["total_payout_krw"] >= wd["payout_krw"], "명세에 지급 반영")
    w.orders["minji"] = done


def journey_4_taehyun(w: World) -> None:
    """④ 김태현 (29, 앱 스타트업 그로스 마케터) — "예산만 정해두고 크리에이터 제안을 받아 고르고 싶다"
    브랜드 가입 → 역경매 공고 → 지원 2건 접수 → 견적 비교 → 한 명 수락·결제 → 공고 마감"""
    b = w.person("taehyun", "김태현", "BRAND")
    b.login()
    s, m = w.people["seoyeon"], w.people["minji"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    campaign = b.api.ok(
        "POST", "/campaign/campaigns", "역경매 공고 등록", expect=201,
        json_body={"title": "가계부 앱 런칭 숏폼 크리에이터 모집", "description": "앱 사용 장면이 들어간 30초 숏폼. 2주 내 게시.",
                   "platform": "INSTAGRAM", "budget_krw": 400_000, "deadline_at": deadline, "target_category": "테크"},
    )
    check(campaign["status"] == "OPEN", "공고 OPEN", campaign["status"])
    Client(w.http).expect("GET", "/campaign/campaigns", 401, "공고 목록은 로그인 전용(화면 안내와 일치)")
    feed = s.api.ok("GET", "/campaign/campaigns", "크리에이터가 보는 공고 목록")
    check(any(c["id"] == campaign["id"] for c in feed), "목록에 공고 노출")
    mine = b.api.ok("GET", "/campaign/my/campaigns", "내 공고 목록")
    check(any(c["id"] == campaign["id"] for c in mine), "내 공고에 포함")
    b.api.expect("POST", f"/campaign/campaigns/{campaign['id']}/applications", 403, "브랜드 계정은 지원 불가",
                 json_body={"message": "브랜드가 지원해 봅니다.", "proposed_price_krw": 1})
    for creator, price in ((s, 350_000), (m, 380_000)):
        app = creator.api.ok(
            "POST", f"/campaign/campaigns/{campaign['id']}/applications", f"{creator.name} 지원 {price:,}원", expect=201,
            json_body={"message": f"{creator.name}입니다. 앱 리뷰 숏폼 경험이 많습니다. 2주 내 게시 가능합니다.", "proposed_price_krw": price},
        )
        check(app["creator_slug"] == creator.slug, "지원서에 크리에이터 슬러그")
    s.api.expect("POST", f"/campaign/campaigns/{campaign['id']}/applications", 409, "중복 지원 차단",
                 json_body={"message": "한 번 더 지원합니다.", "proposed_price_krw": 1})
    apps = b.api.ok("GET", f"/campaign/campaigns/{campaign['id']}/applications", "지원자 견적순 비교", params={"sort": "price_asc"})
    check(len(apps) == 2 and apps[0]["proposed_price_krw"] <= apps[1]["proposed_price_krw"], "지원 2건 · 견적 오름차순")
    s.api.expect("GET", f"/campaign/campaigns/{campaign['id']}/applications", 403, "지원자는 남의 지원서 못 봄")
    chosen = apps[0]
    checkout = b.api.ok("POST", "/payment/checkouts/application", "지원 수락 체크아웃", expect=201,
                        json_body={"application_id": chosen["id"], "requirements": "앱 다운로드 링크 캡션에 포함해 주세요."})
    check(checkout["amount_krw"] > chosen["proposed_price_krw"], "결제액 = 제안가 + 브랜드 수수료")
    confirmed = pay(b, checkout, "지원 수락")
    order = b.api.ok("GET", f"/order/orders/{confirmed['order_id']}", "생성된 주문")
    check(order["amount_krw"] == chosen["proposed_price_krw"], "주문 금액 = 제안 견적", f"{order['amount_krw']:,}")
    b.api.expect("POST", "/payment/checkouts/application", 404, "이미 수락한 지원 재결제 차단",
                 json_body={"application_id": chosen["id"], "requirements": "다시"})
    chosen_person = s if chosen["creator_slug"] == s.slug else m
    mine = chosen_person.api.ok("GET", "/campaign/my/applications", f"{chosen_person.name}: 내 지원 내역")
    row = next((a for a in mine if a["campaign_id"] == campaign["id"]), {})
    check(row.get("order_id") == order["id"], "지원 내역에 주문 연결")
    closed = b.api.ok("POST", f"/campaign/campaigns/{campaign['id']}/close", "공고 마감")
    check(closed["status"] == "CLOSED", "CLOSED", closed["status"])
    other = m if chosen_person is s else s
    other.api.expect("POST", f"/campaign/campaigns/{campaign['id']}/applications", 409, "마감 공고 지원 차단",
                     json_body={"message": "늦었지만 지원합니다.", "proposed_price_krw": 100_000})
    complete_order(b, chosen_person, order["id"])
    w.orders["taehyun"] = order


def journey_5_haeun(w: World) -> None:
    """⑤ 정하은 (38, 뷰티 브랜드 마케팅 팀장) — "정해진 패키지 말고 조건을 협의해서 맞춤 주문하고 싶다"
    브랜드 가입 → 채팅 문의 → 왕복 대화·사진 → 크리에이터 맞춤 오퍼 → 오퍼 결제 → 주문 채팅방"""
    b = w.person("haeun", "정하은", "BRAND")
    b.login()
    s = w.people["seoyeon"]
    conv = b.api.ok("POST", "/chat/conversations", "박서연에게 문의 시작", expect=201, json_body={"creator_slug": s.slug})
    check(conv["counterpart_name"] == s.name, "상대 이름 = 박서연")
    again = b.api.ok("POST", "/chat/conversations", "같은 상대 재문의", expect=201, json_body={"creator_slug": s.slug})
    check(again["id"] == conv["id"], "대화방 중복 생성 없음(기존 방 재사용)")
    b.api.ok("POST", f"/chat/conversations/{conv['id']}/messages", "브랜드 메시지", expect=201,
             json_body={"body": "안녕하세요, 신제품 세럼 릴스 2건 + 스토리 3건을 묶어서 진행 가능할까요?"})
    b.api.ok("POST", f"/chat/conversations/{conv['id']}/photos", "제품 사진 전송", expect=201,
             files={"file": ("serum.png", png_bytes(color=(240, 200, 210)), "image/png")})
    inbox = s.api.ok("GET", "/chat/conversations", "박서연: 대화 목록")
    row = next((c for c in inbox if c["id"] == conv["id"]), {})
    check(row.get("unread_count") == 2, "박서연 안 읽음 2건", str(row.get("unread_count")))
    s.api.ok("POST", f"/chat/conversations/{conv['id']}/read", "박서연 읽음 처리", expect=204)
    s.api.ok("POST", f"/chat/conversations/{conv['id']}/messages", "박서연 답장", expect=201,
             json_body={"body": "가능합니다. 묶음으로 55만원에 오퍼 보내드릴게요."})
    messages = b.api.ok("GET", f"/chat/conversations/{conv['id']}/messages", "브랜드: 메시지 조회")
    check(len(messages) == 3 and any(m["image_url"] for m in messages), "메시지 3건(사진 포함)")
    b.api.expect("POST", f"/chat/conversations/{conv['id']}/offers", 403, "브랜드는 오퍼 못 보냄",
                 json_body={"title": "역제안", "price_krw": 100})
    offer = s.api.ok("POST", f"/chat/conversations/{conv['id']}/offers", "박서연 맞춤 오퍼", expect=201,
                     json_body={"title": "세럼 릴스 2건 + 스토리 3건", "price_krw": 550_000, "revision_limit": 1, "usage_rights": "브랜드 SNS 6개월"})
    check(offer["status"] == "PENDING", "오퍼 PENDING(결제 대기)", offer["status"])
    checkout = b.api.ok("POST", "/payment/checkouts/offer", "오퍼 체크아웃", expect=201,
                        json_body={"offer_id": offer["id"], "requirements": "릴스 1건은 제품 사용 전후 비교로."})
    confirmed = pay(b, checkout, "맞춤 오퍼")
    order = b.api.ok("GET", f"/order/orders/{confirmed['order_id']}", "오퍼 주문")
    check(order["amount_krw"] == 550_000 and order["revision_limit"] == 1, "주문 금액·수정 횟수 = 오퍼 조건")
    check(order["usage_rights"] == "브랜드 SNS 6개월", "2차 활용 범위 이관")
    offers = b.api.ok("GET", f"/chat/conversations/{conv['id']}/offers", "오퍼 목록")
    check(offers[0]["status"] == "PAID" and offers[0]["order_id"] == order["id"], "오퍼 PAID + 주문 연결")
    b.api.expect("POST", "/payment/checkouts/offer", 404, "결제된 오퍼 재결제 차단",
                 json_body={"offer_id": offer["id"], "requirements": "다시"})
    order_conv = b.api.ok("POST", f"/chat/conversations/order/{order['id']}", "주문 채팅방 열기", expect=201)
    check(order_conv["id"] == conv["id"], "주문 채팅방 = 기존 협상방 재사용")
    w.orders["haeun"] = order


def journey_6_jihoon(w: World) -> None:
    """⑥ 오지훈 (41, 광고 대행사 AE, 신중함) — "문제가 생기면 돈을 돌려받을 수 있는지 확인하고 싶다"
    브랜드 가입 → 주문 → 결과물 불만족 → 분쟁 → 운영자 환불 판정 → 크레딧 → 크레딧으로 재주문"""
    b = w.person("jihoon", "오지훈", "BRAND")
    b.login()
    s = w.people["seoyeon"]
    order = order_package(b, s.package_id, "오지훈 → 박서연 주문")
    reason = "브리프와 다른 제품이 노출됐고 광고 표기가 빠졌습니다."
    b.api.expect("POST", f"/order/orders/{order['id']}/disputes", 422, "분쟁 사유 10자 미만 거부", json_body={"reason": "미리"})
    b.api.expect("POST", f"/order/orders/{order['id']}/disputes", 409, "수락 전에는 분쟁 불가", json_body={"reason": reason})
    s.api.ok("POST", f"/order/orders/{order['id']}/accept", "박서연 수락")
    deliver_and_submit(s, order["id"])
    dispute = b.api.ok("POST", f"/order/orders/{order['id']}/disputes", "분쟁 제기", expect=201, json_body={"reason": reason})
    check(dispute["status"] == "OPEN", "분쟁 OPEN", dispute["status"])
    b.api.expect("POST", f"/order/orders/{order['id']}/disputes", 409, "중복 분쟁 차단", json_body={"reason": reason})
    # 분쟁이 열린 채로 브랜드가 승인하면 주문은 COMPLETED가 되고 분쟁은 운영자가 환불 판정을 내릴 수
    # 없는 상태(취소 불가)로 남는다 — 승인이 막히거나 분쟁이 함께 닫혀야 한다
    b.api.expect("POST", f"/order/orders/{order['id']}/approve", 409, "분쟁 OPEN 중 브랜드 승인 보류")
    s.api.ok("POST", f"/order/orders/{order['id']}/cancel-request", "박서연 취소 요청")
    b.api.expect("POST", f"/order/orders/{order['id']}/cancel-consent", 409, "분쟁 OPEN 중 취소 동의 보류")
    fresh = b.api.ok("GET", f"/order/orders/{order['id']}", "분쟁 중 주문 상태")
    check(fresh["status"] == "IN_REVIEW", "분쟁 중 주문은 검토 상태 유지", fresh["status"])
    opened = w.admin.api.ok("GET", "/admin/disputes/open", "운영자 미결 분쟁 목록")
    check(any(d["id"] == dispute["id"] for d in opened), "미결 목록에 포함")
    creator_before = balance(s)
    verdict = w.admin.api.ok("POST", f"/admin/disputes/{dispute['id']}/refund", "운영자: 브랜드 환불 판정")
    check(verdict["status"] == "RESOLVED" and verdict["resolution"] == "REFUND", "판정 RESOLVED/REFUND", str(verdict.get("resolution")))
    after = b.api.ok("GET", f"/order/orders/{order['id']}", "판정 후 주문")
    check(after["status"] == "CANCELLED", "주문 CANCELLED", after["status"])
    credit = balance(b)
    check(credit == order["brand_total_krw"], "브랜드 크레딧 = 결제 총액 전액", f"{credit:,}")
    check(balance(s) == creator_before, "크리에이터 잔액 변동 없음")

    checkout = b.api.ok("POST", "/payment/checkouts", "크레딧으로 재주문 체크아웃", expect=201,
                        json_body={"package_id": s.package_id, "requirements": "이번엔 브리프대로 부탁드립니다.", "use_credit": True})
    check(checkout["credit_applied_krw"] == checkout["amount_krw"] and checkout["pg_amount_krw"] == 0, "전액 크레딧 → PG 청구 0원")
    confirmed = pay(b, checkout, "전액 크레딧")
    check(balance(b) == credit - checkout["credit_applied_krw"], "크레딧 차감 확인")
    b.api.ok("GET", f"/order/orders/{confirmed['order_id']}", "크레딧 주문 조회")
    w.orders["jihoon"] = after


def journey_7_sohee(w: World) -> None:
    """⑦ 한소희 (25, 여행 크리에이터, 부업) — "한 번 반려됐지만 고쳐서 다시 통과하고, 바쁠 땐 주문을 잠그고 싶다"
    가입 → 프로필 반려(사유) → 수정·재제출 → 승인 → 주문 수신 끄기(주문 차단) → 다시 켜기"""
    p = w.person("sohee", "한소희", "CREATOR")
    p.login()
    register_creator(p, "여행", "국내 소도시 브이로그", "부산")
    add_package(p, "TIKTOK", "틱톡 여행 숏폼 1건", 120_000)
    pending = w.admin.api.ok("GET", "/admin/profiles/pending", "심사 대기")
    row = next(r for r in pending if r["slug"] == p.slug)
    check(row["vetting_passed"] is False, "지표 미제출 → 검증 미통과 표시", str(row["vetting_passed"]))
    rejected = w.admin.api.ok("POST", f"/admin/profiles/{row['id']}/reject", "운영자 반려", json_body={"reason": "채널 지표 스크린샷이 없습니다."})
    check(rejected["status"] == "REJECTED", "REJECTED", rejected["status"])
    mine = p.api.ok("GET", "/creator/my/profile", "반려 사유 확인")
    check(mine["rejection_reason"] == "채널 지표 스크린샷이 없습니다.", "반려 사유 전달")
    p.api.ok("POST", "/creator/my/analytics", "지표 제출", expect=201,
             files={"file": ("tiktok.png", png_bytes(color=(0, 0, 0)), "image/png")},
             data={"platform": "TIKTOK", "followers_count": "8000", "engagement_permille": "60"})
    p.api.ok("PUT", "/creator/my/profile", "프로필 보완", json_body={
        "name": p.name, "tagline": "국내 소도시 브이로그 · 틱톡 8천", "bio": "지표 첨부했습니다. 매주 2편 업로드합니다.",
        "location": "부산", "primary_category": "여행"})
    resubmitted = p.api.ok("POST", "/creator/my/profile/resubmit", "재심사 요청")
    check(resubmitted["status"] == "PENDING" and resubmitted["rejection_reason"] is None, "재제출 → PENDING · 사유 초기화")
    row = approve_profile(w.admin, p)
    check(row["vetting_passed"] is True, "보완 후 검증 통과")

    toggled = p.api.ok("PUT", "/creator/my/profile/accepting-orders", "주문 수신 끄기", json_body={"accepting": False})
    check(toggled["accepting_orders"] is False, "accepting_orders=false")
    b = w.people["junho"]
    b.api.expect("POST", "/payment/checkouts", 404, "수신 꺼진 크리에이터 주문 차단",
                 json_body={"package_id": p.package_id, "requirements": "가능할까요?"})
    public = Client(w.http).ok("GET", f"/creator/profiles/{p.slug}", "공개 프로필")
    check(public["accepting_orders"] is False, "공개 프로필에도 주문 불가 표시")
    p.api.ok("PUT", "/creator/my/profile/accepting-orders", "주문 수신 켜기", json_body={"accepting": True})
    b.api.ok("POST", "/payment/checkouts", "다시 켠 뒤 체크아웃 가능", expect=201,
             json_body={"package_id": p.package_id, "requirements": "확인용"})


def journey_8_jaewon(w: World) -> None:
    """⑧ 윤재원 (36, 에이전시 미디어 바이어) — "여러 명에게 한 번에 발주하고, 변동 사항도 처리하고 싶다"
    브랜드 가입 → 장바구니 3건 일괄 결제 → 추가 금액 요청 승인·결제 → 다른 건 거절·환불 → 요청 거절"""
    b = w.person("jaewon", "윤재원", "BRAND")
    b.login()
    s, m, h = w.people["seoyeon"], w.people["minji"], w.people["sohee"]
    b.api.expect("POST", "/payment/checkouts/cart", 422, "빈 장바구니 차단", json_body={"package_ids": [], "requirements": "x"})
    checkout = b.api.ok("POST", "/payment/checkouts/cart", "장바구니 3건 체크아웃", expect=201,
                        json_body={"package_ids": [s.package_id, m.package_id, h.package_id], "requirements": "봄 시즌 캠페인 공통 브리프 참고"})
    confirmed = pay(b, checkout, "장바구니")
    ids = confirmed["order_ids"]
    check(len(ids) == 3, "주문 3건 생성", str(ids))
    orders = {o["creator_user_id"]: o for o in (b.api.ok("GET", f"/order/orders/{i}", f"주문 {i}") for i in ids)}
    check(sum(o["brand_total_krw"] for o in orders.values()) == checkout["amount_krw"], "3건 합계 = 결제액")
    check(all(o["requirements"].startswith("봄 시즌") for o in orders.values()), "공통 브리프 각 주문에 적용")

    # 박서연: 추가 작업 → 금액 변경 요청 → 브랜드 추가 결제
    os_ = orders[s.user_id]
    s.api.expect("POST", f"/order/orders/{os_['id']}/adjustments", 409, "수락 전 금액 변경 불가", json_body={"extra_amount_krw": 1, "reason": "x"})
    s.api.ok("POST", f"/order/orders/{os_['id']}/accept", "박서연 수락")
    adj = s.api.ok("POST", f"/order/orders/{os_['id']}/adjustments", "박서연 추가 금액 5만원 요청", expect=201,
                   json_body={"extra_amount_krw": 50_000, "reason": "스토리 2건 추가 요청분"})
    check(adj["status"] == "REQUESTED", "요청 REQUESTED", adj["status"])
    s.api.expect("POST", f"/order/orders/{os_['id']}/adjustments", 409, "대기 중 중복 요청 차단", json_body={"extra_amount_krw": 1, "reason": "또"})
    listed = b.api.ok("GET", f"/order/orders/{os_['id']}/adjustments", "브랜드: 변경 요청 확인")
    check(listed[0]["reason"] == "스토리 2건 추가 요청분", "요청 사유 전달")
    adj_checkout = b.api.ok("POST", "/payment/checkouts/adjustment", "추가 결제 체크아웃", expect=201, json_body={"adjustment_id": adj["id"]})
    check(adj_checkout["amount_krw"] == 55_000, "추가 결제액 = 5만 + 브랜드 수수료 10%", f"{adj_checkout['amount_krw']:,}")
    pay(b, adj_checkout, "추가 금액")
    grown = b.api.ok("GET", f"/order/orders/{os_['id']}", "증액된 주문")
    check(grown["amount_krw"] == os_["amount_krw"] + 50_000, "주문 금액 +5만", f"{grown['amount_krw']:,}")
    check(grown["brand_total_krw"] == os_["brand_total_krw"] + 55_000, "브랜드 총액 +5.5만")
    check(grown["status"] == "IN_PROGRESS", "증액 후에도 IN_PROGRESS")

    # 최민지: 일정이 안 맞아 거절 → 브랜드 크레딧 환불
    om = orders[m.user_id]
    credit_before = balance(b)
    rejected = m.api.ok("POST", f"/order/orders/{om['id']}/reject", "최민지 거절")
    check(rejected["status"] == "REFUNDED", "REFUNDED", rejected["status"])
    check(balance(b) - credit_before == om["brand_total_krw"], "거절분 전액 크레딧 환불")
    m.api.expect("POST", f"/order/orders/{om['id']}/accept", 409, "거절한 주문 뒤늦은 수락 차단")

    # 한소희: 추가 금액 요청을 브랜드가 거절
    oh = orders[h.user_id]
    h.api.ok("POST", f"/order/orders/{oh['id']}/accept", "한소희 수락")
    adj2 = h.api.ok("POST", f"/order/orders/{oh['id']}/adjustments", "한소희 추가 금액 요청", expect=201,
                    json_body={"extra_amount_krw": 30_000, "reason": "촬영지 이동 비용"})
    h.api.expect("POST", f"/order/adjustments/{adj2['id']}/decline", 403, "크리에이터 본인은 거절 불가")
    declined = b.api.ok("POST", f"/order/adjustments/{adj2['id']}/decline", "브랜드 거절")
    check(declined["status"] == "DECLINED", "DECLINED", declined["status"])
    b.api.expect("POST", "/payment/checkouts/adjustment", 404, "거절된 요청 결제 차단", json_body={"adjustment_id": adj2["id"]})
    unchanged = b.api.ok("GET", f"/order/orders/{oh['id']}", "한소희 주문")
    check(unchanged["amount_krw"] == oh["amount_krw"], "거절 후 금액 그대로")
    w.orders["jaewon"] = grown


def journey_9_doyun(w: World) -> None:
    """⑨ 강도윤 (33, 이벤트 대행 프리랜서) — "일정이 틀어져 주문을 합의 취소하고, 이상한 프로필은 신고하고 싶다"
    브랜드 가입 → 주문 → 취소 요청 거절 → 상대 취소 요청 → 동의 → 전액 크레딧 → 프로필 신고 → 운영자 처리"""
    b = w.person("doyun", "강도윤", "BRAND")
    b.login()
    h = w.people["sohee"]
    order = order_package(b, h.package_id, "강도윤 → 한소희 주문")
    b.api.expect("POST", f"/order/orders/{order['id']}/cancel-request", 409, "수락 전 취소 요청 불가(거절·만료 경로)")
    h.api.ok("POST", f"/order/orders/{order['id']}/accept", "한소희 수락")
    requested = b.api.ok("POST", f"/order/orders/{order['id']}/cancel-request", "브랜드 취소 요청")
    check(requested["cancel_requested_by"] == b.user_id, "취소 요청자 기록")
    b.api.expect("POST", f"/order/orders/{order['id']}/cancel-consent", 403, "요청자 본인 동의 불가")
    declined = h.api.ok("POST", f"/order/orders/{order['id']}/cancel-decline", "한소희 취소 거절")
    check(declined["cancel_requested_by"] is None and declined["status"] == "IN_PROGRESS", "거절 → 요청 해제·작업 계속")
    h.api.ok("POST", f"/order/orders/{order['id']}/cancel-request", "한소희가 취소 요청")
    credit_before = balance(b)
    cancelled = b.api.ok("POST", f"/order/orders/{order['id']}/cancel-consent", "브랜드 동의")
    check(cancelled["status"] == "CANCELLED", "CANCELLED", cancelled["status"])
    check(balance(b) - credit_before == order["brand_total_krw"], "합의 취소 → 전액 크레딧")
    check(balance(h) == 0, "크리에이터 정산 없음")
    b.api.expect("POST", f"/review/orders/{order['id']}/review", 409, "취소 주문 리뷰 불가",
                 json_body={"communication_score": 1, "timeliness_score": 1, "satisfaction_score": 1, "comment": "취소됨"})

    profile = Client(w.http).ok("GET", f"/creator/profiles/{h.slug}", "신고 대상 프로필")
    report = b.api.ok("POST", "/admin/reports", "프로필 신고", expect=201,
                      json_body={"target_type": "PROFILE", "target_id": profile["id"], "reason": "팔로워 수가 실제 채널과 다릅니다."})
    check(report["status"] == "OPEN", "신고 OPEN", report["status"])
    opened = w.admin.api.ok("GET", "/admin/reports/open", "운영자 미처리 신고")
    check(any(r["id"] == report["id"] for r in opened), "미처리 목록 포함")
    resolved = w.admin.api.ok("POST", f"/admin/reports/{report['id']}/resolve", "운영자 처리", json_body={"note": "채널 확인 결과 이상 없음"})
    check(resolved["status"] == "RESOLVED" and resolved["resolution_note"], "RESOLVED + 처리 메모")
    logs = w.admin.api.ok("GET", "/admin/audit-logs", "감사 로그")
    check(any("신고" in (l["subject"] + l["note"]) for l in logs), "신고 처리 감사 로그 남음")
    w.orders["doyun"] = cancelled


def journey_10_jiwoo(w: World) -> None:
    """⑩ 서지우 (30, 푸드 크리에이터) — "알림으로 주문을 챙기고, 다 정리한 뒤 깔끔하게 탈퇴하고 싶다"
    가입·승인 → 주문 알림 수신·읽음 → 탈퇴 시도(진행 주문·잔액 차단) → 완료·인출 → 토큰 회전·로그아웃 → 탈퇴"""
    p = w.person("jiwoo", "서지우", "CREATOR")
    p.login()
    register_creator(p, "푸드", "동네 맛집 · 홈쿡 레시피", "대구")
    add_package(p, "NAVER_BLOG", "블로그 체험 리뷰 1건", 90_000)
    approve_profile(w.admin, p)
    b = w.people["junho"]
    order = order_package(b, p.package_id, "이준호 → 서지우 블로그 주문")
    relay_notifications()
    notes = p.api.ok("GET", "/notification/notifications", "서지우 알림함")
    placed = [n for n in notes["items"] if n["event_type"] == "order.placed"]
    check(len(placed) >= 1 and f"/dashboard/orders/{order['id']}" in placed[0]["link"], "새 주문 알림 + 주문 상세 링크", str(placed[:1]))
    check(notes["unread_count"] >= 1, "안 읽음 1건 이상")
    p.api.ok("POST", f"/notification/notifications/{placed[0]['id']}/read", "알림 하나 읽음", expect=204)
    p.api.ok("POST", "/notification/notifications/read-all", "전부 읽음", expect=204)
    check(p.api.ok("GET", "/notification/notifications", "읽은 뒤 알림함")["unread_count"] == 0, "안 읽음 0")

    p.api.expect("POST", "/auth/account/delete", 409, "진행 중 주문 있으면 탈퇴 차단", json_body={"refresh_token": ""})
    complete_order(b, p, order["id"])
    p.api.expect("POST", "/auth/account/delete", 409, "잔액 남아 있으면 탈퇴 차단", json_body={"refresh_token": ""})
    amount = balance(p)
    wd = p.api.ok("POST", "/order/withdrawals", "잔액 인출", expect=201,
                  json_body={"amount_krw": amount, "bank_name": "토스뱅크", "account_number": "1000-1234-5678", "account_holder": p.name})
    w.admin.api.ok("POST", f"/admin/withdrawals/{wd['id']}/complete", "운영자 지급")
    relay_notifications()
    notes = p.api.ok("GET", "/notification/notifications", "정산 알림")
    check(any(n["event_type"].startswith("withdrawal") for n in notes["items"]), "인출 완료 알림 도착", str([n["event_type"] for n in notes["items"]]))

    rotated = p.api.ok("POST", "/auth/tokens/refresh", "리프레시 토큰 회전", json_body={"refresh_token": p.refresh_token})
    p.api.expect("POST", "/auth/tokens/refresh", 401, "회전된 옛 토큰 재사용 차단", json_body={"refresh_token": p.refresh_token})
    p.refresh_token = rotated["refresh_token"]
    p.api.token = rotated["access_token"]
    p.api.ok("POST", "/auth/tokens/logout", "로그아웃", expect=204, json_body={"refresh_token": p.refresh_token})
    p.api.expect("POST", "/auth/tokens/refresh", 401, "로그아웃 후 리프레시 차단", json_body={"refresh_token": p.refresh_token})
    p.login(expect_new=False)  # 다시 로그인해 탈퇴
    p.api.ok("POST", "/auth/account/delete", "회원 탈퇴", expect=204, json_body={"refresh_token": p.refresh_token})
    p.api.expect("POST", "/auth/tokens/refresh", 401, "탈퇴 후 세션 연장 불가", json_body={"refresh_token": p.refresh_token})
    p.api.expect("GET", "/creator/my/profile", 401, "탈퇴 직후 손에 남은 액세스 토큰 거부(폐기 목록)")
    Client(w.http).expect("GET", f"/creator/profiles/{p.slug}", 404, "탈퇴 후 공개 프로필 비노출")
    listing = Client(w.http).ok("GET", "/creator/profiles", "마켓 목록", params={"q": p.name})
    check(all(i["slug"] != p.slug for i in listing["items"]), "탈퇴 후 목록에서 제외")
    old_user_id = p.user_id
    relogin = p.login(expect_new=True)  # 같은 카카오 계정으로 다시 오면 새 회원
    check(relogin["user"]["id"] != old_user_id, "재가입은 새 계정(id 다름)")
    w.orders["jiwoo"] = order


# ─────────────────────────────── 화면 확인(선택) ───────────────────────────────


def browser_checks(w: World, targets: list[tuple[str, str, str]] | None = None) -> None:
    """여정 끝의 화면 — 각자 자기 목적지 페이지가 로그인 상태로 그려지는지.

    targets: (페르소나 key, 경로, 있어야 할 텍스트). 없으면 기본 10인 여정의 목적지를 쓴다."""
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeout, sync_playwright
    except ImportError:
        check(False, "playwright 미설치 — 화면 확인 건너뜀")
        return
    try:
        if httpx.get(f"{FRONTEND}/", timeout=10).status_code != 200:
            raise httpx.HTTPError("no frontend")
    except httpx.HTTPError:
        check(False, "프론트(:3000) 미기동 — 화면 확인 건너뜀")
        return

    if targets is None:
        targets = []
    if targets == [] and "seoyeon" in w.people:
        targets.append(("seoyeon", "/dashboard/profile", w.people["seoyeon"].name))
        targets.append(("seoyeon", f"/creators/{w.people['seoyeon'].slug}", "데일리 메이크업"))
    for key in ("junho", "minji", "taehyun", "haeun", "jihoon", "jaewon", "doyun"):
        if key in w.people and key in w.orders:
            targets.append((key, f"/dashboard/orders/{w.orders[key]['id']}", w.orders[key]["package_title"]))
    if "minji" in w.people:
        targets.append(("minji", "/dashboard/balance", "인출"))
    if "sohee" in w.people:
        targets.append(("sohee", "/dashboard/packages", "틱톡 여행 숏폼"))
    if "admin" in w.people:
        targets.append(("admin", "/admin", "운영 콘솔"))

    print("\n[화면 확인 — 로그인 상태 렌더]")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        for key, path, text in targets:
            person = w.people[key]
            _current[0] = person.name
            # 리프레시 토큰은 1회용이라 브라우저가 소비한다 — 화면마다 다시 로그인해 새 쌍을 받는다
            try:
                person.login(expect_new=None)
            except StepFailed:
                continue
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            context.add_cookies([{"name": "crecity_refresh", "value": person.refresh_token, "domain": "localhost",
                                  "path": "/api/auth", "httpOnly": True, "sameSite": "Lax"}])
            page = context.new_page()
            problems: list[str] = []
            # 리뷰 조회 404는 "아직 리뷰 없음"을 뜻하는 정상 응답(프론트가 null로 처리) — 문제로 세지 않는다
            page.on("response", lambda r: problems.append(f"{r.status} {r.url[-80:]}")
                    if r.status >= 400 and "/api/" in r.url and not (r.status == 404 and "/review/orders/" in r.url) else None)
            page.goto(f"{FRONTEND}{path}")
            try:
                page.wait_for_selector(f"text={text}", timeout=20_000)
                check(not problems, f"{path} 화면에 '{text}'", "; ".join(problems[:3]))
            except PlaywrightTimeout:
                shot = Path(os.environ.get("TMPDIR", "/tmp")) / f"persona-{key}-{RUN}.png"
                page.screenshot(path=str(shot), full_page=True)
                check(False, f"{path} 화면에 '{text}'", f"미표시 → {shot}")
            context.close()
        browser.close()


# ─────────────────────────────── 조립·실행 ───────────────────────────────


class World:
    """한 번의 실행에서 가입한 사람들과 만든 주문 — 페르소나끼리 서로 거래한다."""

    def __init__(self, http: httpx.Client) -> None:
        self.http = http
        self.people: dict[str, Person] = {}
        self.orders: dict[str, dict] = {}

    def person(self, key: str, name: str, account_type: str) -> Person:
        p = Person(key, name, account_type, self.http)
        self.people[key] = p
        return p

    @property
    def admin(self) -> Person:
        return self.people["admin"]


JOURNEYS: list[tuple[int, str, Any, tuple[int, ...]]] = [
    # (번호, 이름, 함수, 선행 페르소나 번호)
    (1, "박서연 · 뷰티 크리에이터 온보딩", journey_1_seoyeon, ()),
    (2, "이준호 · 첫 주문 완주와 리뷰", journey_2_junho, (1,)),
    (3, "최민지 · 초안 검토와 인출", journey_3_minji, (2,)),
    (4, "김태현 · 역경매 캠페인", journey_4_taehyun, (1, 3)),
    (5, "정하은 · 채팅 협상과 맞춤 오퍼", journey_5_haeun, (1,)),
    (6, "오지훈 · 분쟁 환불과 크레딧 재주문", journey_6_jihoon, (1,)),
    (7, "한소희 · 반려 재제출과 주문 잠금", journey_7_sohee, (2,)),
    (8, "윤재원 · 장바구니와 금액 변경", journey_8_jaewon, (1, 3, 7)),
    (9, "강도윤 · 합의 취소와 신고", journey_9_doyun, (7,)),
    (10, "서지우 · 알림과 탈퇴", journey_10_jiwoo, (2,)),
]


def resolve_selection(only: set[int] | None) -> list[int]:
    if not only:
        return [n for n, *_ in JOURNEYS]
    deps = {n: d for n, _, _, d in JOURNEYS}
    wanted: set[int] = set()
    stack = list(only)
    while stack:
        n = stack.pop()
        if n in wanted:
            continue
        wanted.add(n)
        stack.extend(deps[n])
    return sorted(wanted)


def check_integrity() -> None:
    """여정이 끝난 뒤 원장이 맞아떨어지는지 — smoke.py와 같은 질의."""
    _current[0] = "원장"
    print("\n[데이터 정합성]")
    snippet = """
import asyncio, json
from sqlalchemy import text
from core.database import session_scope
async def main():
    async with session_scope() as s:
        orphan = (await s.execute(text("SELECT count(*) FROM orders o WHERE (SELECT count(*) FROM ledger_entries l WHERE l.order_id=o.id)=0"))).scalar()
        rate = (await s.execute(text("SELECT COALESCE(sum(floor(amount_krw*brand_fee_percent/100.0) + floor(amount_krw*creator_fee_percent/100.0)),0) FROM orders WHERE status='COMPLETED'"))).scalar()
        ledger = (await s.execute(text("SELECT COALESCE(sum(amount_krw),0) FROM ledger_entries WHERE entry_type='PLATFORM_REVENUE'"))).scalar()
    print(json.dumps({'orphan': int(orphan), 'rate': int(rate), 'ledger': int(ledger)}))
asyncio.run(main())
"""
    result = subprocess.run([PY, "-c", snippet], cwd=ROOT / "crecity",
                            env={"PYTHONPATH": ".:apps", "PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    if result.returncode != 0:
        check(False, "DB 정합성 조회", result.stderr.strip()[-300:])
        return
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    check(payload["orphan"] == 0, "원장 없는 주문 0건", f"{payload['orphan']}건")
    check(payload["rate"] == payload["ledger"], "수수료: 요율 계산 == 원장 합", f"{payload['rate']:,} vs {payload['ledger']:,}")


_CLEANUP_SNIPPET = r"""
import asyncio, json, re
from pathlib import Path
from sqlalchemy import text
from core.config import UPLOAD_DIR
from core.database import session_scope
from core.redis import get_redis

async def main():
    removed = {}
    async with session_scope() as s:
        async def q(sql, **kw):
            return await s.execute(text(sql), kw)
        # 페르소나 계정 + 같은 실행에서 탈퇴해 익명화된 계정(id 범위 안의 소프트 삭제 행)
        ids = (await q("SELECT id FROM users WHERE email LIKE '%@persona.crecity.local'")).scalars().all()
        if not ids:
            print(json.dumps({})); return
        lo, hi = min(ids), max(ids)
        deleted = (await q("SELECT id FROM users WHERE deleted_at IS NOT NULL AND id BETWEEN :lo AND :hi", lo=lo, hi=hi)).scalars().all()
        await q("CREATE TEMP TABLE pu (id int PRIMARY KEY) ON COMMIT DROP")
        for i in set(ids) | set(deleted):
            await q("INSERT INTO pu VALUES (:i)", i=i)
        await q("CREATE TEMP TABLE pp ON COMMIT DROP AS SELECT id FROM creator_profiles WHERE user_id IN (SELECT id FROM pu)")
        await q("CREATE TEMP TABLE po ON COMMIT DROP AS SELECT id FROM orders WHERE brand_user_id IN (SELECT id FROM pu) OR creator_user_id IN (SELECT id FROM pu)")
        await q("CREATE TEMP TABLE pc ON COMMIT DROP AS SELECT id FROM conversations WHERE brand_user_id IN (SELECT id FROM pu) OR creator_user_id IN (SELECT id FROM pu)")
        await q("CREATE TEMP TABLE pk ON COMMIT DROP AS SELECT id FROM campaigns WHERE brand_user_id IN (SELECT id FROM pu)")
        await q("CREATE TEMP TABLE pi ON COMMIT DROP AS SELECT id FROM payment_intents WHERE brand_user_id IN (SELECT id FROM pu)")
        await q("CREATE TEMP TABLE pw ON COMMIT DROP AS SELECT id FROM withdrawals WHERE user_id IN (SELECT id FROM pu)")

        # 업로드 파일 — 행을 지우기 전에 이름을 모은다
        files = []
        for table, col, folder, scope in (
            ("portfolio_items", "file_name", "portfolio", "profile_id IN (SELECT id FROM pp)"),
            ("profile_analytics", "screenshot_file_name", "analytics", "profile_id IN (SELECT id FROM pp)"),
            ("order_deliverables", "file_name", "deliverables", "order_id IN (SELECT id FROM po)"),
            ("messages", "image_file_name", "chat", "conversation_id IN (SELECT id FROM pc)"),
        ):
            names = (await q(f"SELECT {col} FROM {table} WHERE {scope} AND {col} IS NOT NULL")).scalars().all()
            files += [Path(UPLOAD_DIR) / folder / n for n in names]

        steps = [
            ("profile_analytics", "profile_id IN (SELECT id FROM pp)"),  # audience_breakdown은 CASCADE
            ("profile_faqs", "profile_id IN (SELECT id FROM pp)"),
            ("profile_view_daily", "profile_id IN (SELECT id FROM pp)"),
            ("portfolio_items", "profile_id IN (SELECT id FROM pp)"),
            ("creator_packages", "profile_id IN (SELECT id FROM pp)"),
            ("order_adjustments", "order_id IN (SELECT id FROM po)"),
            ("order_deliverables", "order_id IN (SELECT id FROM po)"),
            ("order_disputes", "order_id IN (SELECT id FROM po)"),
            ("order_revision_requests", "order_id IN (SELECT id FROM po)"),
            ("order_status_transitions", "order_id IN (SELECT id FROM po)"),
            ("reviews", "order_id IN (SELECT id FROM po)"),
            ("brand_reviews", "order_id IN (SELECT id FROM po)"),
            ("ledger_entries", "order_id IN (SELECT id FROM po) OR withdrawal_id IN (SELECT id FROM pw) OR user_id IN (SELECT id FROM pu)"),
            ("payment_intent_items", "intent_id IN (SELECT id FROM pi)"),
            ("payment_intents", "id IN (SELECT id FROM pi)"),
            ("campaign_applications", "campaign_id IN (SELECT id FROM pk) OR creator_user_id IN (SELECT id FROM pu)"),
            ("campaigns", "id IN (SELECT id FROM pk)"),
            ("messages", "conversation_id IN (SELECT id FROM pc)"),
            ("custom_offers", "conversation_id IN (SELECT id FROM pc)"),
            ("conversation_reads", "conversation_id IN (SELECT id FROM pc)"),
            ("conversations", "id IN (SELECT id FROM pc)"),
            ("notifications", "user_id IN (SELECT id FROM pu)"),
            ("admin_reports", "reporter_user_id IN (SELECT id FROM pu)"),
            ("withdrawals", "id IN (SELECT id FROM pw)"),
            ("outbox_events", " OR ".join([
                "(payload::jsonb->>'brand_user_id')::int IN (SELECT id FROM pu)",
                "(payload::jsonb->>'creator_user_id')::int IN (SELECT id FROM pu)",
                "(payload::jsonb->>'recipient_user_id')::int IN (SELECT id FROM pu)",
                "(payload::jsonb->>'order_id')::int IN (SELECT id FROM po)",
                "(payload::jsonb->>'campaign_id')::int IN (SELECT id FROM pk)",
                "(payload::jsonb->>'profile_id')::int IN (SELECT id FROM pp)",
                "(payload::jsonb->>'conversation_id')::int IN (SELECT id FROM pc)",
            ])),
            ("user_roles", "user_id IN (SELECT id FROM pu)"),
            ("social_identities", "user_id IN (SELECT id FROM pu)"),
            ("orders", "id IN (SELECT id FROM po)"),
            ("creator_profiles", "id IN (SELECT id FROM pp)"),
            ("users", "id IN (SELECT id FROM pu)"),
        ]
        for table, where in steps:
            removed[table] = (await q(f"DELETE FROM {table} WHERE {where}")).rowcount
        # 감사 로그는 자유 텍스트 — 페르소나 운영자 이메일 또는 페르소나 계정 id를 언급한 행
        id_alt = "|".join(str(i) for i in sorted(set(ids) | set(deleted)))
        removed["admin_audit_logs"] = (await q(
            "DELETE FROM admin_audit_logs WHERE note LIKE '%persona.crecity.local%' "
            "OR note ~ :pattern", pattern=rf"(운영자 |user_id=|user=)({id_alt})(\D|$)")).rowcount
        await s.commit()  # session_scope는 커밋하지 않는다 — 여기서 한 트랜잭션으로 확정

    for f in files:
        try:
            f.unlink(); removed["files"] = removed.get("files", 0) + 1
        except FileNotFoundError:
            pass
    # Redis — 리프레시 토큰(값이 user_id)·폐기 목록
    redis = await get_redis()
    targets = set(str(i) for i in set(ids) | set(deleted))
    async for key in redis.scan_iter("auth:refresh:*"):
        if (await redis.get(key)) in targets:
            await redis.delete(key); removed["redis"] = removed.get("redis", 0) + 1
    for i in targets:
        removed["redis"] = removed.get("redis", 0) + await redis.delete(f"auth:revoked-user:{i}")
    await redis.aclose()
    print(json.dumps(removed, ensure_ascii=False))

asyncio.run(main())
"""


def cleanup() -> int:
    """이 스크립트가 만든 계정과 거기 딸린 모든 데이터(주문·원장·대화·파일·Redis 토큰)를 지운다."""
    result = subprocess.run([PY, "-c", _CLEANUP_SNIPPET], cwd=ROOT / "crecity",
                            env={"PYTHONPATH": ".:apps", "PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr.strip()[-1500:], file=sys.stderr)
        return 1
    removed = json.loads(result.stdout.strip().splitlines()[-1])
    if not removed:
        print("정리할 페르소나 데이터가 없습니다.")
        return 0
    for table, count in removed.items():
        if count:
            print(f"  {table:28} {count:>5}건")
    print(f"합계 {sum(removed.values())}건 삭제")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="페르소나 여정 회귀")
    parser.add_argument("--browser", action="store_true", help="여정 끝 화면까지 확인(프론트 :3000 필요)")
    parser.add_argument("--only", help="실행할 페르소나 번호(쉼표 구분) — 선행 페르소나는 자동 포함")
    parser.add_argument("--cleanup", action="store_true", help="여정을 돌리지 않고 페르소나 데이터를 전부 삭제")
    args = parser.parse_args()
    if args.cleanup:
        return cleanup()
    only = {int(x) for x in args.only.split(",")} if args.only else None
    selected = resolve_selection(only)

    print(f"스텁 백엔드 기동(:{PORT}) — OAuth 프로필·PG 승인만 스텁, 나머지는 실제 코드·DB…")
    server = start_stub_backend()
    try:
        with httpx.Client() as http:
            w = World(http)
            _current[0] = "김운영(운영자)"
            print("\n[조연] 김운영 · 운영자")
            journey_admin(w)
            for number, title, fn, _ in JOURNEYS:
                if number not in selected:
                    continue
                _current[0] = title.split(" · ")[0]
                print(f"\n[{number}] {title}")
                print(f"    {fn.__doc__.strip().splitlines()[0]}")
                try:
                    fn(w)
                except StepFailed as stop:
                    print(f"    ⛔ 여정 중단: {stop}")
                except Exception:  # noqa: BLE001 — 한 사람의 사고가 다른 사람의 여정을 막지 않게
                    check(False, "예상치 못한 오류", traceback.format_exc().strip().splitlines()[-1])
                    traceback.print_exc()
            check_integrity()
            if args.browser:
                browser_checks(w)
    finally:
        server.terminate()
        server.wait(timeout=10)

    failures = [(who, label) for ok, who, label in _results if not ok]
    print("\n" + "=" * 70)
    for who, label in failures:
        print(f"  ✕ [{who}] {label}")
    for who, text in _notes:
        print(f"  ⓘ [{who}] {text}")
    print(f"통과 {len(_results) - len(failures)} · 실패 {len(failures)} · 관찰 {len(_notes)} · 실행 접미사 {RUN}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
