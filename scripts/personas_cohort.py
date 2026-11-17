#!/usr/bin/env python3
"""코호트 여정 회귀 — 고객 30명 + 운영자 5명이 세 차례 방문(라운드)하며 서로 얽힌다.

personas.py(10인 단발 여정)의 틀을 그대로 쓰되, 여기서는 **돌아오는 방문**을 본다:
  라운드 1  브랜드는 둘러보고, 크리에이터는 프로필을 올리고, 운영자는 심사한다
  라운드 2  브랜드가 주문·문의·공고를 내고, 크리에이터가 받아 작업하고, 운영자는 분쟁·정산을 처리한다
  라운드 3  브랜드가 승인·리뷰·분쟁·취소를 하고, 크리에이터가 마무리·인출하고, 운영자가 정리한다
매 라운드는 브랜드 → 크리에이터 → 운영자 순서로 돈다. 그래서 라운드 N에 브랜드가 한 일을 같은
라운드에 크리에이터가 받고, 운영자가 처리한 결과를 다음 라운드에 고객이 마주한다.

고객 시나리오는 정상 경로뿐 아니라 특이 경로(금액 위변조, 체크아웃 이탈, 장바구니 중복, 지표 과장,
잠수·만료, 남의 주문 엿보기, 탈퇴 후 재가입, 오퍼 남발…)를 섞었다. 운영자 시나리오는 그 결과로
쌓이는 대기열(심사·지표 재검토·분쟁·신고·인출)을 규칙대로 처리하고, 고객이 선언한 기대와 대조한다.

시간 경과(72h 만료·공고 마감)는 DB의 마감 시각을 과거로 되감고 실제 스윕 스크립트를 돌려 만든다.

실행:
    .venv/bin/python scripts/personas_cohort.py             # API 여정
    .venv/bin/python scripts/personas_cohort.py --browser   # + 화면 확인 (프론트 :3000)
    .venv/bin/python scripts/personas.py --cleanup          # 정리는 personas.py와 같은 명령
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import traceback
from datetime import datetime, timedelta, timezone

import httpx

import personas as base
from personas import (
    BACKEND, PY, ROOT, YEAR, Client, Person, StepFailed, World, add_package, balance, check,
    deliver_and_submit, must, note, pay, png_bytes, register_creator, relay_notifications, run_script,
)

# ─────────────────────────────── 공통 조각 ───────────────────────────────


def onboard(p: Person, category: str, tagline: str, location: str,
            packages: list[tuple[str, str, int, int]], analytics: list[tuple[str, int, int]]) -> None:
    """가입 직후 한 번에 하는 일 — 프로필·패키지·채널 지표. 첫 패키지가 p.package_id."""
    register_creator(p, category, tagline, location)
    first = None
    for platform, title, price, revision_limit in packages:
        pid = add_package(p, platform, title, price, revision_limit)
        first = first or pid
    p.package_id = first or 0
    for platform, followers, engagement in analytics:
        p.api.ok("POST", "/creator/my/analytics", f"{platform} 지표 {followers:,}명·{engagement / 10:.1f}%", expect=201,
                 files={"file": (f"{platform.lower()}.png", png_bytes(), "image/png")},
                 data={"platform": platform, "followers_count": str(followers), "engagement_permille": str(engagement)})


def orders_between(brand: Person, creator: Person) -> list[dict]:
    """브랜드가 그 크리에이터에게 낸 주문들 — 오래된 순."""
    orders = brand.api.ok("GET", "/order/orders", f"{brand.name}: 주문 목록")
    return sorted((o for o in orders if o["creator_user_id"] == creator.user_id), key=lambda o: o["id"])


def latest_order(brand: Person, creator: Person) -> dict:
    found = orders_between(brand, creator)
    must(bool(found), f"{brand.name}→{creator.name} 주문 존재")
    return found[-1]


def time_travel(table: str, ids: list[int]) -> None:
    """마감 시각을 한 시간 전으로 되감는다 — 그 뒤 실제 스윕 스크립트가 만료를 처리한다."""
    snippet = f"""
import asyncio
from sqlalchemy import text
from core.database import session_scope
async def main():
    async with session_scope() as s:
        await s.execute(text("UPDATE {table} SET deadline_at = now() - interval '1 hour' WHERE id = ANY(:ids)"), {{"ids": {ids}}})
        await s.commit()
asyncio.run(main())
"""
    result = subprocess.run([PY, "-c", snippet], cwd=ROOT / "crecity",
                            env={"PYTHONPATH": ".:apps", "PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    must(result.returncode == 0, f"시간 되감기 {table} {ids}", result.stderr.strip()[-200:])
    run_script("order_deadline_sweep.py" if table == "orders" else "campaign_deadline_sweep.py")


class Scenario:
    """페르소나 한 명 — 이름·유형·이야기와 방문 1~3."""

    key = ""
    name = ""
    account_type = "BRAND"
    story = ""

    def visit1(self, w: World, p: Person) -> None: ...
    def visit2(self, w: World, p: Person) -> None: ...
    def visit3(self, w: World, p: Person) -> None: ...


# ─────────────────────────────── 브랜드 14명 ───────────────────────────────


class B01(Scenario):
    key, name, account_type = "b01", "이준호", "BRAND"
    story = "소규모 D2C 대표 · 첫 방문엔 둘러만 보고, 두 번째에 두 명에게 주문, 세 번째에 승인·리뷰"

    def visit1(self, w, p):
        p.login()
        guest = Client(w.http)
        guest.ok("GET", "/order/fee-policy", "수수료 정책 확인")
        cats = p.api.ok("GET", "/creator/categories", "카테고리 목록")
        check("뷰티" in cats, "뷰티 카테고리 존재")
        p.api.ok("GET", "/creator/profiles", "낮은 가격순 탐색", params={"sort": "price_asc", "category": "뷰티"})
        p.api.ok("GET", "/creator/profiles", "팔로워 1만 이상 필터", params={"followers_min": 10000})
        p.api.ok("GET", "/creator/profiles/popular", "인기 크리에이터", params={"limit": 4})
        p.api.expect("GET", "/order/orders", 200, "주문 없음 확인")

    def visit2(self, w, p):
        p.login(expect_new=False)
        for creator in (w.people["c01"], w.people["c21"]):
            listing = p.api.ok("GET", "/creator/profiles", f"{creator.name} 검색", params={"q": creator.name})
            check(any(i["slug"] == creator.slug for i in listing["items"]), f"{creator.name} 승인돼 목록에 보임")
            guest = Client(w.http)
            guest.ok("POST", f"/creator/profiles/{creator.slug}/views", "프로필 열람 기록", expect=204)
            base.order_package(p, creator.package_id, f"{creator.name}에게 주문")

    def visit3(self, w, p):
        p.login(expect_new=False)
        total = 0
        for creator in (w.people["c01"], w.people["c21"]):
            order = latest_order(p, creator)
            check(order["status"] == "IN_REVIEW", f"{creator.name} 제출 완료 상태", order["status"])
            done = p.api.ok("POST", f"/order/orders/{order['id']}/approve", f"{creator.name} 구매 확정")
            total += done["brand_total_krw"]
            p.api.ok("POST", f"/review/orders/{order['id']}/review", f"{creator.name} 리뷰", expect=201,
                     json_body={"communication_score": 5, "timeliness_score": 5, "satisfaction_score": 4, "comment": "기한 안에 깔끔하게 마무리해 주셨어요."})
        report = p.api.ok("GET", f"/order/reports/{YEAR}", "월별 지출 리포트")
        check(bool(report) and any(r["total_krw"] >= total for r in report), "리포트에 이번 달 결제 합 이상 반영", f"{total:,}")


class B02(Scenario):
    key, name, account_type = "b02", "송위조", "BRAND"
    story = "결제 리다이렉트 값을 손보는 브랜드 · 금액 불일치와 중복 승인이 어떻게 막히는지"

    def visit1(self, w, p):
        p.login()
        p.api.expect("POST", "/payment/confirm", 404, "없는 결제 승인 시도", json_body={"payment_key": "x", "pg_order_id": "no-such", "amount_krw": 1})

    def visit2(self, w, p):
        p.login(expect_new=False)
        c = w.people["c01"]
        checkout = p.api.ok("POST", "/payment/checkouts", "체크아웃", expect=201, json_body={"package_id": c.package_id, "requirements": "위변조 테스트 브리프"})
        p.api.expect("POST", "/payment/confirm", 400, "금액을 1원 깎아 승인 → 거부",
                     json_body={"payment_key": "stub", "pg_order_id": checkout["pg_order_id"], "amount_krw": checkout["pg_amount_krw"] - 1})
        p.api.expect("POST", "/payment/confirm", 409, "실패 처리된 결제 재승인 → 이미 처리됨",
                     json_body={"payment_key": "stub", "pg_order_id": checkout["pg_order_id"], "amount_krw": checkout["pg_amount_krw"]})
        check(not orders_between(p, c), "실패한 결제로 주문 생성 안 됨")
        order = base.order_package(p, c.package_id, "정상 재시도")

    def visit3(self, w, p):
        p.login(expect_new=False)
        order = latest_order(p, w.people["c01"])
        check(order["status"] in ("IN_REVIEW", "COMPLETED"), "정상 주문은 진행됨", order["status"])
        check(order["counterpart_completed_orders"] >= 0, "상대 거래 이력 필드 존재")


class B03(Scenario):
    key, name, account_type = "b03", "한이탈", "BRAND"
    story = "결제창까지 갔다가 닫고 나간 브랜드 · 며칠 뒤 돌아와 그 결제를 마치고, 상대가 무응답이라 만료 환불"

    def visit1(self, w, p):
        p.login()
        packages = p.api.ok("GET", "/creator/profiles/haneul-beauty/packages", "시드 크리에이터 패키지")
        must(bool(packages), "시드 패키지 존재")
        self.checkout = p.api.ok("POST", "/payment/checkouts", "체크아웃만 하고 이탈", expect=201,
                                 json_body={"package_id": packages[0]["id"], "requirements": "나중에 다시 올게요"})

    def visit2(self, w, p):
        p.login(expect_new=False)
        confirmed = pay(p, self.checkout, "이전 체크아웃 이어서")
        order = p.api.ok("GET", f"/order/orders/{confirmed['order_id']}", "생성된 주문")
        check(order["status"] == "PENDING_ACCEPT", "수락 대기", order["status"])
        self.order = order
        base.order_package(p, w.people["c22"].package_id, "동시에 c22에게도 주문")  # c22는 이 브랜드가 무응답이라 분쟁을 건다

    def visit3(self, w, p):
        p.login(expect_new=False)
        before = balance(p)
        time_travel("orders", [self.order["id"]])
        expired = p.api.ok("GET", f"/order/orders/{self.order['id']}", "72시간 지난 주문")
        check(expired["status"] == "REFUNDED", "무응답 만료 → REFUNDED", expired["status"])
        check(balance(p) - before == self.order["brand_total_krw"], "만료 환불 전액 크레딧")
        public = Client(w.http).ok("GET", "/creator/profiles/haneul-beauty", "상대 공개 프로필")
        check(public["received_orders"] >= 1, "받은 주문 수 집계")


class B04(Scenario):
    key, name, account_type = "b04", "장중복", "BRAND"
    story = "장바구니에 같은 걸 두 번 담는 브랜드 · 잠수 크리에이터 주문은 만료, 휴가 중 크리에이터는 담기지도 않음"

    def visit1(self, w, p):
        p.login()
        p.api.expect("POST", "/payment/checkouts/cart", 422, "빈 장바구니", json_body={"package_ids": [], "requirements": "x"})

    def visit2(self, w, p):
        p.login(expect_new=False)
        c03, c04 = w.people["c03"], w.people["c04"]
        checkout = p.api.ok("POST", "/payment/checkouts/cart", "같은 패키지 2번 + 잠수 크리에이터", expect=201,
                            json_body={"package_ids": [c03.package_id, c03.package_id, c04.package_id], "requirements": "가을 룩북"})
        confirmed = pay(p, checkout, "장바구니")
        check(len(confirmed["order_ids"]) == 2, "중복은 하나로 합쳐져 주문 2건", str(confirmed["order_ids"]))

    def visit3(self, w, p):
        p.login(expect_new=False)
        c04 = w.people["c04"]
        order = latest_order(p, c04)
        check(order["status"] == "PENDING_ACCEPT", "며칠째 수락 대기", order["status"])
        time_travel("orders", [order["id"]])
        order = p.api.ok("GET", f"/order/orders/{order['id']}", "72시간 지난 주문")
        check(order["status"] == "REFUNDED", "잠수 크리에이터 주문 만료 환불", order["status"])
        check(order["counterpart_accept_expired_orders"] >= 1, "상대 무응답 만료 이력 노출")
        p.api.expect("POST", "/payment/checkouts/cart", 404, "휴가 중 크리에이터 포함 장바구니 거부",
                     json_body={"package_ids": [c04.package_id], "requirements": "다시"})


class B05(Scenario):
    key, name, account_type = "b05", "구부분", "BRAND"
    story = "환불 크레딧을 큰 주문에 일부만 쓰는 브랜드 · 크레딧 + PG 혼합 결제"

    def visit1(self, w, p):
        p.login()
        packages = p.api.ok("GET", "/creator/profiles/haneul-beauty/packages", "시드 패키지")
        self.small = base.order_package(p, min(packages, key=lambda x: x["price_krw"])["id"], "작은 주문(무응답 예정)")

    def visit2(self, w, p):
        p.login(expect_new=False)
        time_travel("orders", [self.small["id"]])
        credit = balance(p)
        check(credit == self.small["brand_total_krw"], "만료 환불 크레딧 확보", f"{credit:,}")
        c06 = w.people["c06"]
        big = max(p.api.ok("GET", f"/creator/profiles/{c06.slug}/packages", "c06 패키지"), key=lambda x: x["price_krw"])
        checkout = p.api.ok("POST", "/payment/checkouts", "크레딧 일부 사용 체크아웃", expect=201,
                            json_body={"package_id": big["id"], "requirements": "혼합 결제", "use_credit": True})
        check(checkout["credit_applied_krw"] == credit and checkout["pg_amount_krw"] == checkout["amount_krw"] - credit, "크레딧 전액 + 나머지 PG")
        confirmed = pay(p, checkout, "혼합")
        check(balance(p) == 0, "크레딧 소진")
        self.big = p.api.ok("GET", f"/order/orders/{confirmed['order_id']}", "혼합 결제 주문")

    def visit3(self, w, p):
        p.login(expect_new=False)
        order = p.api.ok("GET", f"/order/orders/{self.big['id']}", "혼합 결제 주문 확인")
        check(order["brand_total_krw"] == self.big["brand_total_krw"], "총액 보존")
        if order["status"] == "IN_REVIEW":
            p.api.ok("POST", f"/order/orders/{order['id']}/approve", "승인")


class B06(Scenario):
    key, name, account_type = "b06", "최극단", "BRAND"
    story = "별점을 극단으로 주고 수정 요청도 한도까지 밀어붙이는 브랜드 · 추가 금액 요청은 거절"

    def visit1(self, w, p):
        p.login()

    def visit2(self, w, p):
        p.login(expect_new=False)
        base.order_package(p, w.people["c07"].package_id, "c07(수정 1회 한도) 주문")
        base.order_package(p, w.people["c11"].package_id, "c11 주문")

    def visit3(self, w, p):
        p.login(expect_new=False)
        c07, c11 = w.people["c07"], w.people["c11"]
        o7 = latest_order(p, c07)
        adjustments = p.api.ok("GET", f"/order/orders/{o7['id']}/adjustments", "c07 추가 금액 요청 확인")
        must(bool(adjustments), "추가 금액 요청 도착")
        p.api.ok("POST", f"/order/adjustments/{adjustments[0]['id']}/decline", "추가 금액 거절")
        p.api.ok("POST", f"/order/orders/{o7['id']}/request-revision", "수정 요청 1회", json_body={"comment": "자막 폰트를 바꿔 주세요."})
        p.api.expect("POST", f"/order/orders/{o7['id']}/request-revision", 422, "5자 미만 수정 코멘트 거부", json_body={"comment": "또"})
        p.api.expect("POST", f"/order/orders/{o7['id']}/request-revision", 409, "작업 중 상태라 2회째 즉시 요청 불가", json_body={"comment": "색감도 다시 봐 주세요."})
        o11 = latest_order(p, c11)
        p.api.ok("POST", f"/order/orders/{o11['id']}/approve", "c11 승인")
        bad = {"communication_score": 0, "timeliness_score": 1, "satisfaction_score": 1, "comment": "x"}
        p.api.expect("POST", f"/review/orders/{o11['id']}/review", 422, "0점 리뷰 거부", json_body=bad)
        bad["communication_score"] = 6
        p.api.expect("POST", f"/review/orders/{o11['id']}/review", 422, "6점 리뷰 거부", json_body=bad)
        p.api.ok("POST", f"/review/orders/{o11['id']}/review", "1점 리뷰", expect=201,
                 json_body={"communication_score": 1, "timeliness_score": 1, "satisfaction_score": 1, "comment": "기대 이하였습니다."})
        p.api.expect("POST", f"/review/orders/{o11['id']}/review", 409, "리뷰 수정 대신 재작성 시도 차단",
                     json_body={"communication_score": 5, "timeliness_score": 5, "satisfaction_score": 5, "comment": "다시 생각해보니"})


class B07(Scenario):
    key, name, account_type = "b07", "오공고", "BRAND"
    story = "공고를 여러 개 올리는 스타트업 · 마감일 실수, 지원자 없는 마감, 시간 지나 자동 마감, 둘 다 수락"

    def visit1(self, w, p):
        p.login()
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        p.api.expect("POST", "/campaign/campaigns", 422, "지난 마감일 공고 거부",
                     json_body={"title": "과거 마감", "description": "실수", "platform": "INSTAGRAM", "budget_krw": 100000, "deadline_at": past})
        soon = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        self.auto = p.api.ok("POST", "/campaign/campaigns", "곧 마감되는 공고", expect=201,
                             json_body={"title": "이번 주 마감 숏폼", "description": "빠르게", "platform": "TIKTOK", "budget_krw": 200000, "deadline_at": soon})
        self.empty = p.api.ok("POST", "/campaign/campaigns", "지원자 없을 공고", expect=201,
                              json_body={"title": "라이브 커머스 진행자", "description": "경험자", "platform": "YOUTUBE", "budget_krw": 900000})
        self.main = p.api.ok("POST", "/campaign/campaigns", "메인 공고", expect=201,
                             json_body={"title": "가계부 앱 릴스 크리에이터 모집", "description": "앱 사용 장면 30초", "platform": "INSTAGRAM", "budget_krw": 400000, "target_category": "테크"})

    def visit2(self, w, p):
        p.login(expect_new=False)
        closed = p.api.ok("POST", f"/campaign/campaigns/{self.empty['id']}/close", "지원자 없는 공고 마감")
        check(closed["status"] == "CLOSED", "CLOSED")
        p.api.expect("POST", f"/campaign/campaigns/{self.empty['id']}/close", 409, "이미 마감된 공고 재마감")
        time_travel("campaigns", [self.auto["id"]])
        auto = p.api.ok("GET", f"/campaign/campaigns/{self.auto['id']}", "마감일 지난 공고")
        check(auto["status"] == "CLOSED", "마감일 경과 → 자동 CLOSED", auto["status"])

    def visit3(self, w, p):
        p.login(expect_new=False)
        apps = p.api.ok("GET", f"/campaign/campaigns/{self.main['id']}/applications", "메인 공고 지원자", params={"sort": "price_asc"})
        check(len(apps) == 2, "지원 2건", str(len(apps)))
        for app in apps:
            checkout = p.api.ok("POST", "/payment/checkouts/application", f"{app['creator_name']} 수락", expect=201,
                                json_body={"application_id": app["id"], "requirements": "앱 링크 캡션 포함"})
            pay(p, checkout, app["creator_name"])
        apps = p.api.ok("GET", f"/campaign/campaigns/{self.main['id']}/applications", "수락 후 지원자")
        check(all(a["order_id"] for a in apps), "둘 다 주문 연결")
        p.api.ok("POST", f"/campaign/campaigns/{self.main['id']}/close", "메인 공고 마감")


class B08(Scenario):
    key, name, account_type = "b08", "박도배", "BRAND"
    story = "채팅으로 메시지를 도배하고 허위 프로필을 신고하는 브랜드 · 상대가 대화방을 신고한다"

    def visit1(self, w, p):
        p.login()
        p.api.expect("POST", "/chat/conversations", 404, "없는 크리에이터 문의", json_body={"creator_slug": "no-such-creator"})

    def visit2(self, w, p):
        p.login(expect_new=False)
        c10 = w.people["c10"]
        conv = p.api.ok("POST", "/chat/conversations", "c10에게 문의", expect=201, json_body={"creator_slug": c10.slug})
        self.conv_id = conv["id"]
        p.api.expect("POST", f"/chat/conversations/{conv['id']}/messages", 422, "빈 메시지 거부", json_body={"body": "   "})
        for i in range(5):
            p.api.ok("POST", f"/chat/conversations/{conv['id']}/messages", f"도배 {i + 1}", expect=201, json_body={"body": f"답장 주세요!!! ({i + 1})"})
        profile = Client(w.http).ok("GET", f"/creator/profiles/{w.people['c01'].slug}", "c01 프로필")
        p.api.ok("POST", "/admin/reports", "c01 허위 프로필 신고", expect=201,
                 json_body={"target_type": "PROFILE", "target_id": profile["id"], "reason": "팔로워 수가 실제와 다른 것 같습니다."})

    def visit3(self, w, p):
        p.login(expect_new=False)
        messages = p.api.ok("GET", f"/chat/conversations/{self.conv_id}/messages", "대화 다시 열기")
        check(sum(1 for m in messages if m["is_mine"]) == 5, "내 메시지 5건 보존")
        p.api.ok("POST", f"/chat/conversations/{self.conv_id}/messages", "하나 더", expect=201, json_body={"body": "죄송합니다, 급해서요."})


class B09(Scenario):
    key, name, account_type = "b09", "나악평", "BRAND"
    story = "크리에이터들에게 나쁜 평가를 받는 브랜드 · 다음 크리에이터가 브랜드 평판을 볼 수 있는가"

    def visit1(self, w, p):
        p.login()
        rating = Client(w.http).ok("GET", f"/review/brands/{p.user_id}/rating", "평판 없음")
        check(rating["total"] == 0, "거래 전 평판 0건")

    def visit2(self, w, p):
        p.login(expect_new=False)
        for key in ("c11", "c18"):
            base.order_package(p, w.people[key].package_id, f"{w.people[key].name} 주문", requirements="요구사항은 나중에 알려드릴게요")

    def visit3(self, w, p):
        p.login(expect_new=False)
        for key in ("c11", "c18"):
            order = latest_order(p, w.people[key])
            if order["status"] == "IN_REVIEW":
                p.api.ok("POST", f"/order/orders/{order['id']}/approve", f"{w.people[key].name} 승인")
            else:
                check(False, f"{w.people[key].name} 주문 제출 상태", order["status"])


class B10(Scenario):
    key, name, account_type = "b10", "다발주", "BRAND"
    story = "세 명에게 한 번에 발주하고 한 명은 승인, 한 명은 취소 요청, 한 명은 근거 없는 분쟁"

    def visit1(self, w, p):
        p.login()

    def visit2(self, w, p):
        p.login(expect_new=False)
        ids = [w.people[k].package_id for k in ("c06", "c10", "c16")]
        checkout = p.api.ok("POST", "/payment/checkouts/cart", "3인 장바구니", expect=201, json_body={"package_ids": ids, "requirements": "봄 시즌 공통 브리프"})
        confirmed = pay(p, checkout, "3인")
        check(len(confirmed["order_ids"]) == 3, "주문 3건")

    def visit3(self, w, p):
        p.login(expect_new=False)
        o6 = latest_order(p, w.people["c06"])
        check(p.api.ok("POST", f"/order/orders/{o6['id']}/approve", "c06 승인")["status"] == "COMPLETED", "COMPLETED")
        o10 = latest_order(p, w.people["c10"])
        req = p.api.ok("POST", f"/order/orders/{o10['id']}/cancel-request", "c10 취소 요청")
        check(req["cancel_requested_by"] == p.user_id, "취소 요청 대기")
        o16 = latest_order(p, w.people["c16"])
        p.api.ok("POST", f"/order/orders/{o16['id']}/disputes", "c16 근거 없는 분쟁(기각 예정)", expect=201,
                 json_body={"reason": "그냥 마음에 안 듭니다. 기각되어도 어쩔 수 없습니다."})
        w.expect_dispute[o16["id"]] = "DISMISS"


class B11(Scenario):
    key, name, account_type = "b11", "염탐꾼", "BRAND"
    story = "남의 주문·대화·분쟁·결제를 들여다보려는 브랜드 · 모든 문이 닫혀 있어야 한다"

    def visit1(self, w, p):
        p.login()
        for path in ("/admin/orders", "/admin/profiles/pending", "/admin/disputes/open", "/admin/withdrawals/pending"):
            p.api.expect("GET", path, 403, f"운영 API {path}")
        status, _ = p.api.call("GET", "/order/orders/1")
        check(status in (403, 404), "남의(시드) 주문 상세", str(status))
        status, _ = p.api.call("GET", "/creator/my/profile")
        check(status in (403, 404), "브랜드가 크리에이터 프로필 API", str(status))

    def visit2(self, w, p):
        p.login(expect_new=False)
        other = latest_order(w.people["b01"], w.people["c01"])
        p.api.expect("GET", f"/order/orders/{other['id']}", 403, "다른 브랜드 주문 상세")
        p.api.expect("GET", f"/order/orders/{other['id']}/deliverables", 403, "다른 브랜드 납품물")
        p.api.expect("POST", f"/order/orders/{other['id']}/approve", 403, "남의 주문 승인")
        p.api.expect("POST", f"/order/orders/{other['id']}/disputes", 403, "남의 주문 분쟁", json_body={"reason": "내 주문도 아닌데 분쟁을 겁니다."})
        conv_id = w.scenarios["b08"].conv_id
        p.api.expect("GET", f"/chat/conversations/{conv_id}/messages", 403, "남의 대화 열람")
        p.api.expect("POST", f"/chat/conversations/{conv_id}/messages", 403, "남의 대화에 끼어들기", json_body={"body": "안녕"})
        checkout = w.scenarios["b03"].checkout
        p.api.expect("POST", "/payment/confirm", 403, "남의 결제 승인 시도",
                     json_body={"payment_key": "x", "pg_order_id": checkout["pg_order_id"], "amount_krw": checkout["pg_amount_krw"]})

    def visit3(self, w, p):
        p.login(expect_new=False)
        other = latest_order(w.people["b10"], w.people["c10"])
        p.api.expect("POST", f"/order/orders/{other['id']}/cancel-consent", 403, "남의 취소 요청에 동의")
        p.api.expect("GET", f"/order/orders/{other['id']}/disputes", 403, "남의 분쟁 이력")
        p.api.expect("POST", f"/campaign/campaigns/{w.scenarios['b07'].main['id']}/close", 403, "남의 공고 마감")


class B12(Scenario):
    key, name, account_type = "b12", "문지출", "BRAND"
    story = "지출을 관리하는 브랜드 · 초안 검토를 깜빡해 자동 컨펌, 파일로 납품받고 리포트로 대조"

    def visit1(self, w, p):
        p.login()

    def visit2(self, w, p):
        p.login(expect_new=False)
        base.order_package(p, w.people["c19"].package_id, "c19(초안 검토) 주문")
        base.order_package(p, w.people["c21"].package_id, "c21(파일 납품) 주문")

    def visit3(self, w, p):
        p.login(expect_new=False)
        o19 = latest_order(p, w.people["c19"])
        check(o19["status"] == "DRAFT_REVIEW", "초안 검토 대기 중", o19["status"])
        time_travel("orders", [o19["id"]])
        o19 = p.api.ok("GET", f"/order/orders/{o19['id']}", "72시간 지난 초안")
        check(o19["status"] == "IN_PROGRESS" and o19["draft_approved"] is True, "무응답 → 초안 자동 컨펌", o19["status"])
        o21 = latest_order(p, w.people["c21"])
        files = p.api.ok("GET", f"/order/orders/{o21['id']}/deliverables", "c21 납품물")
        check(any(d["kind"] == "FILE" for d in files), "파일 납품물 포함")
        p.api.ok("POST", f"/order/orders/{o21['id']}/approve", "c21 승인")
        report = p.api.ok("GET", f"/order/reports/{YEAR}", "지출 리포트")
        check(bool(report), "리포트 행 존재")


class B13(Scenario):
    key, name, account_type = "b13", "정후회", "BRAND"
    story = "결제하자마자 후회해 취소하려는 브랜드 · 수락 전엔 취소가 없어 채팅으로 거절을 부탁, 오퍼 협상도"

    def visit1(self, w, p):
        p.login()

    def visit2(self, w, p):
        p.login(expect_new=False)
        c18, c25 = w.people["c18"], w.people["c25"]
        order = base.order_package(p, c18.package_id, "c18 주문")
        p.api.expect("POST", f"/order/orders/{order['id']}/cancel-request", 409, "수락 전 취소 요청 불가")
        conv = p.api.ok("POST", f"/chat/conversations/order/{order['id']}", "주문 채팅방", expect=201)
        p.api.ok("POST", f"/chat/conversations/{conv['id']}/messages", "거절 부탁", expect=201, json_body={"body": "죄송한데 실수로 결제했어요. 거절해 주시면 감사하겠습니다."})
        conv2 = p.api.ok("POST", "/chat/conversations", "c25 협상 문의", expect=201, json_body={"creator_slug": c25.slug})
        self.conv2 = conv2["id"]
        p.api.ok("POST", f"/chat/conversations/{conv2['id']}/messages", "조건 제안", expect=201, json_body={"body": "릴스 2건 묶음으로 견적 주실 수 있나요?"})

    def visit3(self, w, p):
        p.login(expect_new=False)
        c18 = w.people["c18"]
        first = orders_between(p, c18)[0]
        check(first["status"] == "REFUNDED", "c18이 거절해 환불", first["status"])
        credit = balance(p)
        checkout = p.api.ok("POST", "/payment/checkouts", "크레딧으로 c18 재주문", expect=201,
                            json_body={"package_id": c18.package_id, "requirements": "이번엔 진짜입니다", "use_credit": True})
        check(checkout["pg_amount_krw"] == 0 and checkout["credit_applied_krw"] == credit, "전액 크레딧")
        pay(p, checkout, "재주문")
        offers = p.api.ok("GET", f"/chat/conversations/{self.conv2}/offers", "c25 오퍼 목록")
        check(len(offers) == 3, "오퍼 3건 도착", str(len(offers)))
        cheapest = min(offers, key=lambda o: o["price_krw"])
        checkout = p.api.ok("POST", "/payment/checkouts/offer", "가장 싼 오퍼 결제", expect=201, json_body={"offer_id": cheapest["id"], "requirements": "묶음 진행"})
        pay(p, checkout, "오퍼")
        offers = p.api.ok("GET", f"/chat/conversations/{self.conv2}/offers", "결제 후 오퍼 목록")
        check(sum(1 for o in offers if o["status"] == "PAID") == 1 and sum(1 for o in offers if o["status"] == "PENDING") == 2, "하나만 PAID, 둘은 그대로")


class B14(Scenario):
    key, name, account_type = "b14", "김세션", "BRAND"
    story = "폰과 노트북을 오가며 로그인하는 브랜드 · 토큰 회전·로그아웃·탈퇴·재가입"

    def visit1(self, w, p):
        p.login()
        phone = p.refresh_token
        laptop = p.login(expect_new=False)["refresh_token"]
        rotated = p.api.ok("POST", "/auth/tokens/refresh", "폰 토큰 회전", json_body={"refresh_token": phone})
        p.api.expect("POST", "/auth/tokens/refresh", 401, "회전된 폰 토큰 재사용", json_body={"refresh_token": phone})
        p.api.ok("POST", "/auth/tokens/refresh", "노트북 토큰은 독립적으로 유효", json_body={"refresh_token": laptop})
        self.phone = rotated["refresh_token"]

    def visit2(self, w, p):
        p.login(expect_new=False)
        p.api.ok("POST", "/auth/tokens/logout", "폰에서 로그아웃", expect=204, json_body={"refresh_token": self.phone})
        p.api.expect("POST", "/auth/tokens/refresh", 401, "로그아웃한 폰 토큰", json_body={"refresh_token": self.phone})
        rotated = p.api.ok("POST", "/auth/tokens/refresh", "노트북 세션은 살아 있음", json_body={"refresh_token": p.refresh_token})
        p.refresh_token = rotated["refresh_token"]

    def visit3(self, w, p):
        p.login(expect_new=False)
        old_id = p.user_id
        p.api.ok("POST", "/auth/account/delete", "주문 없는 브랜드 탈퇴", expect=204, json_body={"refresh_token": p.refresh_token})
        p.api.expect("GET", "/order/orders", 401, "탈퇴 직후 토큰 거부")
        p.account_type = "CREATOR"
        p.login(expect_new=True)
        check(p.user_id != old_id and p.account_type == "CREATOR", "재가입은 새 계정, 이번엔 크리에이터")


# ─────────────────────────────── 크리에이터 16명 ───────────────────────────────


class C01(Scenario):
    key, name, account_type = "c01", "유하늘", "CREATOR"
    story = "신입 뷰티 크리에이터 · 표준 온보딩 → 첫 주문 두 건 → 리뷰 답글과 첫 인출"

    def visit1(self, w, p):
        p.login()
        onboard(p, "뷰티", "데일리 메이크업 · 스킨케어", "서울",
                [("INSTAGRAM", "인스타 피드 1건 + 스토리", 150_000, 2)], [("INSTAGRAM", 15_000, 45)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        mine = p.api.ok("GET", "/creator/my/profile", "내 프로필")
        check(mine["status"] == "APPROVED", "심사 통과", mine["status"])
        orders = p.api.ok("GET", "/order/orders", "받은 주문")
        pending = [o for o in orders if o["status"] == "PENDING_ACCEPT"]
        check(len(pending) == 2, "b01·b02 주문 2건 도착", str(len(pending)))
        for o in pending:
            p.api.ok("POST", f"/order/orders/{o['id']}/accept", f"주문 {o['id']} 수락")
            deliver_and_submit(p, o["id"])

    def visit3(self, w, p):
        p.login(expect_new=False)
        reviews = p.api.ok("GET", f"/review/creators/{p.slug}", "내 리뷰")
        check(reviews["total"] >= 1, "리뷰 도착")
        for item in reviews["items"]:
            if item["can_reply"]:
                p.api.ok("POST", f"/review/reviews/{item['id']}/reply", "답글", expect=201, json_body={"reply": "감사합니다!"})
        amount = balance(p)
        check(amount > 0, "정산 적립", f"{amount:,}")
        p.api.ok("POST", "/order/withdrawals", "첫 인출", expect=201,
                 json_body={"amount_krw": amount, "bank_name": "카카오뱅크", "account_number": "3333-11-1111111", "account_holder": p.name})


class C02(Scenario):
    key, name, account_type = "c02", "허과장", "CREATOR"
    story = "팔로워 200만·참여율 90%라고 적는 크리에이터 · 이상치로 잡혀 반려, 현실적인 지표로 고쳐 통과"

    def visit1(self, w, p):
        p.login()
        onboard(p, "라이프", "글로벌 메가 인플루언서", "서울", [("INSTAGRAM", "메가 노출 패키지", 5_000_000, 0)], [("INSTAGRAM", 2_000_000, 900)])
        w.expect_review[p.slug] = "REJECTED"
        w.expect_flag[p.slug] = "KEEP"

    def visit2(self, w, p):
        p.login(expect_new=False)
        mine = p.api.ok("GET", "/creator/my/profile", "심사 결과")
        check(mine["status"] == "REJECTED" and mine["rejection_reason"], "이상치 사유로 반려", str(mine["rejection_reason"]))
        p.api.ok("POST", "/creator/my/analytics", "현실적인 지표로 재제출", expect=201,
                 files={"file": ("real.png", png_bytes(), "image/png")},
                 data={"platform": "INSTAGRAM", "followers_count": "20000", "engagement_permille": "40"})
        p.api.ok("POST", "/creator/my/profile/resubmit", "재심사 요청")
        w.expect_review[p.slug] = "APPROVED"

    def visit3(self, w, p):
        p.login(expect_new=False)
        mine = p.api.ok("GET", "/creator/my/profile", "재심사 결과")
        check(mine["status"] == "APPROVED", "고친 뒤 승인", mine["status"])
        Client(w.http).expect("GET", f"/creator/profiles/{p.slug}/analytics", 401, "지표는 비로그인 열람 불가(가입 게이트)")
        public = w.people["b01"].api.ok("GET", f"/creator/profiles/{p.slug}/analytics", "로그인한 브랜드가 보는 지표")
        check(public and public[0]["followers_count"] == 20_000, "공개 지표는 고친 값")


class C03(Scenario):
    key, name, account_type = "c03", "오실수", "CREATOR"
    story = "입력 실수가 잦은 크리에이터 · 슬러그·플랫폼·가격 오류를 거치고, 지표 없이 내 반려 → 보완 통과 → 패키지 손질"

    def visit1(self, w, p):
        p.login()
        body = {"slug": "My Slug!", "name": p.name, "tagline": "여행 브이로그", "bio": "소도시 여행을 기록합니다.", "location": "부산", "primary_category": "여행"}
        p.api.expect("POST", "/creator/profiles", 422, "대문자·공백 슬러그 거부", json_body=body)
        body["slug"] = "kim-beauty"
        p.api.expect("POST", "/creator/profiles", 409, "남이 쓰는 슬러그 거부", json_body=body)
        body["slug"] = p.slug
        p.api.ok("POST", "/creator/profiles", "제대로 등록", expect=201, json_body=body)
        p.api.expect("POST", "/creator/profiles", 409, "계정당 프로필 1개", json_body={**body, "slug": p.slug + "-2"})
        pkg = {"platform": "FACEBOOK", "title": "페북 포스트", "description": "x", "price_krw": 50_000}
        p.api.expect("POST", f"/creator/profiles/{p.slug}/packages", 422, "지원 안 하는 플랫폼", json_body=pkg)
        pkg.update(platform="TIKTOK", price_krw=0)
        p.api.expect("POST", f"/creator/profiles/{p.slug}/packages", 422, "0원 패키지", json_body=pkg)
        add_package(p, "TIKTOK", "틱톡 여행 숏폼 1건", 120_000)
        self.second = add_package(p, "INSTAGRAM", "릴스 1건", 90_000)
        p.package_id = p.api.ok("GET", f"/creator/profiles/{p.slug}/packages", "패키지 목록")[0]["id"]
        w.expect_review[p.slug] = "REJECTED"  # 지표를 안 냈다

    def visit2(self, w, p):
        p.login(expect_new=False)
        mine = p.api.ok("GET", "/creator/my/profile", "심사 결과")
        check(mine["status"] == "REJECTED", "지표 미제출 반려", mine["status"])
        p.api.expect("POST", "/creator/my/profile/resubmit", 200, "고치지 않고 재제출(다시 반려될 것)")
        w.expect_review[p.slug] = "REJECTED"

    def visit3(self, w, p):
        p.login(expect_new=False)
        mine = p.api.ok("GET", "/creator/my/profile", "두 번째 심사 결과")
        check(mine["status"] == "REJECTED", "안 고치면 또 반려", mine["status"])
        p.api.ok("POST", "/creator/my/analytics", "이번엔 지표 제출", expect=201,
                 files={"file": ("tt.png", png_bytes(), "image/png")}, data={"platform": "TIKTOK", "followers_count": "8000", "engagement_permille": "60"})
        p.api.ok("POST", "/creator/my/profile/resubmit", "세 번째 재심사")
        w.expect_review[p.slug] = "APPROVED"
        updated = p.api.ok("PUT", f"/creator/packages/{p.package_id}", "패키지 가격 인상",
                           json_body={"platform": "TIKTOK", "title": "틱톡 여행 숏폼 1건", "description": "x", "price_krw": 140_000, "revision_limit": 2, "usage_rights": ""})
        check(updated["price_krw"] == 140_000, "가격 반영")
        p.api.ok("DELETE", f"/creator/packages/{self.second}", "두 번째 패키지 삭제", expect=204)
        p.api.expect("DELETE", f"/creator/packages/{self.second}", 404, "이미 삭제한 패키지")
        campaign = w.scenarios["b07"].main
        p.api.expect("POST", f"/campaign/campaigns/{campaign['id']}/applications", 409, "마감된 공고 지원 불가",
                     json_body={"message": "늦었지만 지원합니다 정말로", "proposed_price_krw": 100_000})


class C04(Scenario):
    key, name, account_type = "c04", "강잠수", "CREATOR"
    story = "프로필만 올리고 사라지는 크리에이터 · 두 번째 방문은 없고, 세 번째에 와 보니 주문이 만료돼 있다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "패션", "스트릿 룩북", "서울", [("INSTAGRAM", "룩북 피드 3장", 200_000, 1)], [("INSTAGRAM", 30_000, 30)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        # 잠깐 들어와 주문함은 열어보지도 않고 수신만 끄고 나간다
        p.login(expect_new=False)
        p.api.ok("PUT", "/creator/my/profile/accepting-orders", "당분간 주문 받지 않기", json_body={"accepting": False})

    def visit3(self, w, p):
        p.login(expect_new=False)
        expired = [o for o in p.api.ok("GET", "/order/orders", "밀린 주문") if o["status"] == "REFUNDED"]
        must(bool(expired), "무응답으로 만료된 주문 존재")
        check(expired[0]["status"] == "REFUNDED", "무응답 72h → 환불", expired[0]["status"])
        p.api.expect("POST", f"/order/orders/{expired[0]['id']}/accept", 409, "뒤늦은 수락 불가")
        relay_notifications()
        notes = p.api.ok("GET", "/notification/notifications", "알림함")
        check(any(n["event_type"] == "order.placed" for n in notes["items"]), "놓친 주문 알림은 남아 있음")


class C06(Scenario):
    key, name, account_type = "c06", "박멀티", "CREATOR"
    story = "네 플랫폼을 다 하는 크리에이터 · 팔로워가 급증해 재검토에 걸리지만 운영자가 확인 후 해제"

    def visit1(self, w, p):
        p.login()
        onboard(p, "테크", "가젯 리뷰 · 앱 소개", "판교",
                [("INSTAGRAM", "인스타 릴스 1건", 250_000, 2), ("YOUTUBE", "유튜브 리뷰 1편", 800_000, 2), ("TIKTOK", "틱톡 1건", 150_000, 2), ("NAVER_BLOG", "블로그 리뷰", 120_000, 2)],
                [("INSTAGRAM", 12_000, 40), ("YOUTUBE", 50_000, 30), ("TIKTOK", 20_000, 80), ("NAVER_BLOG", 3_000, 20)])
        w.expect_review[p.slug] = "APPROVED"
        rates = Client(w.http).ok("GET", "/creator/market-rates", "시장 시세")
        check(isinstance(rates, list), "시세 목록")

    def visit2(self, w, p):
        p.login(expect_new=False)
        surged = p.api.ok("POST", "/creator/my/analytics", "인스타 팔로워 4배 급증 갱신", expect=201,
                          files={"file": ("ig2.png", png_bytes(), "image/png")}, data={"platform": "INSTAGRAM", "followers_count": "50000", "engagement_permille": "38"})
        check(surged["followers_count"] == 50_000, "덮어쓰기(같은 플랫폼 1행)")
        w.expect_flag[p.slug] = "CLEAR"
        p.api.ok("DELETE", "/creator/my/analytics/TIKTOK", "틱톡 접음", expect=204)
        check(len(p.api.ok("GET", "/creator/my/analytics", "지표 목록")) == 3, "플랫폼 3개")
        for o in p.api.ok("GET", "/order/orders", "받은 주문"):
            if o["status"] == "PENDING_ACCEPT":
                p.api.ok("POST", f"/order/orders/{o['id']}/accept", f"주문 {o['id']} 수락")
                deliver_and_submit(p, o["id"], "https://youtu.be/multi")

    def visit3(self, w, p):
        p.login(expect_new=False)
        public = Client(w.http).ok("GET", f"/creator/profiles/{p.slug}", "공개 프로필")
        check(public["followers_total"] == 50_000 + 50_000 + 3_000, "팔로워 합계 = 3플랫폼", str(public["followers_total"]))
        done = [o for o in p.api.ok("GET", "/order/orders", "주문") if o["status"] == "COMPLETED"]
        check(len(done) >= 1, "완료 주문 존재")


class C07(Scenario):
    key, name, account_type = "c07", "윤한도", "CREATOR"
    story = "수정 1회만 받는 크리에이터 · 추가 금액을 요청했다 거절당하고, 수정 요청을 받은 뒤 취소를 원한다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "푸드", "홈쿡 레시피 쇼츠", "대구", [("YOUTUBE", "쇼츠 1편 (수정 1회)", 300_000, 1)], [("YOUTUBE", 40_000, 25)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        order = next(o for o in p.api.ok("GET", "/order/orders", "주문") if o["status"] == "PENDING_ACCEPT")
        p.api.ok("POST", f"/order/orders/{order['id']}/accept", "수락")
        p.api.ok("POST", f"/order/orders/{order['id']}/adjustments", "추가 촬영 비용 요청", expect=201, json_body={"extra_amount_krw": 80_000, "reason": "재료비 추가"})
        deliver_and_submit(p, order["id"], "https://youtu.be/shorts-1")
        self.order_id = order["id"]

    def visit3(self, w, p):
        p.login(expect_new=False)
        adj = p.api.ok("GET", f"/order/orders/{self.order_id}/adjustments", "추가 금액 요청 결과")
        check(adj[0]["status"] == "DECLINED", "브랜드가 거절", adj[0]["status"])
        order = p.api.ok("GET", f"/order/orders/{self.order_id}", "주문")
        check(order["status"] == "IN_PROGRESS" and order["revisions_used"] == 1, "수정 요청 1회 받음")
        revs = p.api.ok("GET", f"/order/orders/{self.order_id}/revisions", "수정 내용")
        check("폰트" in revs[0]["comment"], "수정 코멘트 확인")
        p.api.ok("POST", f"/order/orders/{self.order_id}/submit", "수정본 제출")
        req = p.api.ok("POST", f"/order/orders/{self.order_id}/cancel-request", "더는 못 하겠다 — 취소 요청")
        check(req["cancel_requested_by"] == p.user_id, "취소 요청 대기(브랜드 응답 필요)")


class C08(Scenario):
    key, name, account_type = "c08", "임지원", "CREATOR"
    story = "공고만 노리는 크리에이터 · 마감된 공고엔 못 넣고, 열린 공고에 넣어 수락받는다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "테크", "앱 소개 릴스 전문", "서울", [("INSTAGRAM", "앱 릴스 1건", 350_000, 2)], [("INSTAGRAM", 25_000, 50)])
        w.expect_review[p.slug] = "APPROVED"
        p.api.expect("POST", "/campaign/campaigns", 403, "크리에이터는 공고를 못 올림",
                     json_body={"title": "x", "description": "x", "platform": "INSTAGRAM", "budget_krw": 1})

    def visit2(self, w, p):
        p.login(expect_new=False)
        b07 = w.scenarios["b07"]
        p.api.expect("POST", f"/campaign/campaigns/{b07.empty['id']}/applications", 409, "마감된 공고", json_body={"message": "지원합니다 지원합니다", "proposed_price_krw": 100_000})
        p.api.expect("POST", f"/campaign/campaigns/{b07.main['id']}/applications", 422, "너무 짧은 제안", json_body={"message": "ㅎㅇ", "proposed_price_krw": 100_000})
        p.api.ok("POST", f"/campaign/campaigns/{b07.main['id']}/applications", "메인 공고 지원", expect=201,
                 json_body={"message": "앱 릴스 30편 이상 제작했습니다. 2주 내 게시 가능합니다.", "proposed_price_krw": 320_000})
        c11 = w.people["c11"]
        c11.api.ok("POST", f"/campaign/campaigns/{b07.main['id']}/applications", "c11도 같은 공고 지원", expect=201,
                   json_body={"message": "저도 지원합니다. 견적은 조금 더 높지만 퀄리티로 보답합니다.", "proposed_price_krw": 380_000})

    def visit3(self, w, p):
        p.login(expect_new=False)
        mine = p.api.ok("GET", "/campaign/my/applications", "내 지원 내역")
        row = next(a for a in mine if a["campaign_title"].startswith("가계부"))
        check(row["order_id"] is not None and row["campaign_status"] == "CLOSED", "수락돼 주문 연결 · 공고 마감")
        p.api.ok("POST", f"/order/orders/{row['order_id']}/accept", "공고 주문 수락")
        deliver_and_submit(p, row["order_id"], "https://www.instagram.com/reel/app-launch/")


class C10(Scenario):
    key, name, account_type = "c10", "서신고", "CREATOR"
    story = "도배 메시지에 시달려 대화방을 신고하는 크리에이터 · 취소 요청은 단호히 거절"

    def visit1(self, w, p):
        p.login()
        onboard(p, "뷰티", "쿨톤 메이크업", "인천", [("INSTAGRAM", "메이크업 릴스", 180_000, 2)], [("INSTAGRAM", 9_000, 55)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        inbox = p.api.ok("GET", "/chat/conversations", "대화 목록")
        spam = next(c for c in inbox if c["unread_count"] >= 5)
        p.api.ok("POST", "/admin/reports", "도배 대화방 신고", expect=201,
                 json_body={"target_type": "CONVERSATION", "target_id": spam["id"], "reason": "같은 메시지를 반복해서 보냅니다."})
        p.api.ok("POST", f"/chat/conversations/{spam['id']}/read", "읽음", expect=204)
        for o in p.api.ok("GET", "/order/orders", "주문"):
            if o["status"] == "PENDING_ACCEPT":
                p.api.ok("POST", f"/order/orders/{o['id']}/accept", "b10 주문 수락")
                p.api.ok("POST", f"/order/orders/{o['id']}/deliverables/links", "중간 결과 링크", expect=201, json_body={"url": "https://example.com/wip", "caption": "작업 중"})

    def visit3(self, w, p):
        p.login(expect_new=False)
        order = next(o for o in p.api.ok("GET", "/order/orders", "주문") if o["cancel_requested_by"])
        declined = p.api.ok("POST", f"/order/orders/{order['id']}/cancel-decline", "취소 거절")
        check(declined["cancel_requested_by"] is None and declined["status"] == "IN_PROGRESS", "작업 계속")
        p.api.ok("POST", f"/order/orders/{order['id']}/submit", "최종 제출")


class C11(Scenario):
    key, name, account_type = "c11", "조평가", "CREATOR"
    story = "1점 리뷰를 받고 답글을 다는 크리에이터 · 무례한 브랜드에는 1점 평가로 되돌려준다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "라이프", "미니멀 라이프 브이로그", "제주", [("YOUTUBE", "브이로그 PPL 1편", 400_000, 2)], [("YOUTUBE", 60_000, 20)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        for o in p.api.ok("GET", "/order/orders", "주문"):
            if o["status"] == "PENDING_ACCEPT":
                p.api.ok("POST", f"/order/orders/{o['id']}/accept", f"{o['counterpart_name']} 주문 수락")
                deliver_and_submit(p, o["id"], "https://youtu.be/vlog")

    def visit3(self, w, p):
        p.login(expect_new=False)
        reviews = p.api.ok("GET", f"/review/creators/{p.slug}", "내 리뷰")
        one_star = next((r for r in reviews["items"] if r["overall_score"] <= 1.5), None)
        must(one_star is not None, "1점 리뷰 도착")
        p.api.ok("POST", f"/review/reviews/{one_star['id']}/reply", "정중한 답글", expect=201, json_body={"reply": "피드백 감사합니다. 다음엔 더 신경 쓰겠습니다."})
        p.api.expect("POST", f"/review/reviews/{one_star['id']}/reply", 409, "답글 두 번 불가", json_body={"reply": "또"})
        for o in p.api.ok("GET", "/order/orders", "주문"):
            if o["status"] == "COMPLETED" and o["brand_user_id"] == w.people["b09"].user_id:
                p.api.ok("POST", f"/review/orders/{o['id']}/brand-review", "b09에게 1점", expect=201, json_body={"score": 1, "comment": "요구사항을 끝까지 안 줬습니다."})
        rating = Client(w.http).ok("GET", f"/review/brands/{w.people['b09'].user_id}/rating", "b09 평판")
        check(rating["total"] >= 1 and rating["average_score"] <= 2, "나쁜 평판 반영", str(rating))


class C16(Scenario):
    key, name, account_type = "c16", "문분쟁", "CREATOR"
    story = "근거 없는 분쟁을 당한 크리에이터 · 분쟁 중엔 아무것도 못 하고 운영자 기각을 기다린다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "패션", "빈티지 코디", "서울", [("INSTAGRAM", "코디 피드 2장", 130_000, 2)], [("INSTAGRAM", 11_000, 35)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        for o in p.api.ok("GET", "/order/orders", "주문"):
            if o["status"] == "PENDING_ACCEPT":
                p.api.ok("POST", f"/order/orders/{o['id']}/accept", "수락")
                deliver_and_submit(p, o["id"])
                self.order_id = o["id"]

    def visit3(self, w, p):
        p.login(expect_new=False)
        disputes = p.api.ok("GET", f"/order/orders/{self.order_id}/disputes", "내 주문 분쟁")
        check(disputes and disputes[0]["status"] == "OPEN", "분쟁 OPEN — 운영자 판정 대기")
        p.api.expect("POST", f"/order/orders/{self.order_id}/cancel-request", 200, "분쟁 중에도 취소 요청은 남길 수 있음")


class C18(Scenario):
    key, name, account_type = "c18", "한거절", "CREATOR"
    story = "부탁받으면 거절해 주는 크리에이터 · 요구사항 없는 브랜드 주문은 받고, 재주문은 반긴다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "여행", "캠핑 · 차박", "강원", [("YOUTUBE", "차박 브이로그 PPL", 350_000, 2)], [("YOUTUBE", 45_000, 22)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        b13, b09 = w.people["b13"], w.people["b09"]
        for o in p.api.ok("GET", "/order/orders", "주문"):
            if o["status"] != "PENDING_ACCEPT":
                continue
            if o["brand_user_id"] == b13.user_id:
                rejected = p.api.ok("POST", f"/order/orders/{o['id']}/reject", "실수 결제 거절")
                check(rejected["status"] == "REFUNDED", "REFUNDED")
            else:
                p.api.ok("POST", f"/order/orders/{o['id']}/accept", "b09 주문 수락")
                deliver_and_submit(p, o["id"], "https://youtu.be/camping")

    def visit3(self, w, p):
        p.login(expect_new=False)
        pending = [o for o in p.api.ok("GET", "/order/orders", "주문") if o["status"] == "PENDING_ACCEPT"]
        check(len(pending) == 1, "b13 재주문 도착", str(len(pending)))
        for o in pending:
            p.api.ok("POST", f"/order/orders/{o['id']}/accept", "재주문 수락")
        for o in p.api.ok("GET", "/order/orders", "주문"):
            if o["status"] == "COMPLETED":
                p.api.ok("POST", f"/review/orders/{o['id']}/brand-review", "b09 평가 2점", expect=201, json_body={"score": 2, "comment": "소통이 느렸어요."})


class C19(Scenario):
    key, name, account_type = "c19", "정초안", "CREATOR"
    story = "초안을 올려두고 답을 기다리는 크리에이터 · 브랜드가 잊어 자동 컨펌되면 최종본을 낸다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "테크", "가젯 언박싱", "서울", [("YOUTUBE", "언박싱 1편(초안 검토 포함)", 500_000, 2)], [("YOUTUBE", 80_000, 28)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        order = next(o for o in p.api.ok("GET", "/order/orders", "주문") if o["status"] == "PENDING_ACCEPT")
        p.api.ok("POST", f"/order/orders/{order['id']}/accept", "수락")
        p.api.ok("POST", f"/order/orders/{order['id']}/deliverables/links", "초안 링크", expect=201, json_body={"url": "https://drive.example.com/draft", "caption": "초안"})
        draft = p.api.ok("POST", f"/order/orders/{order['id']}/submit-draft", "초안 제출")
        check(draft["status"] == "DRAFT_REVIEW" and draft["deadline_at"], "검토 대기 + 마감 시각")
        self.order_id = order["id"]

    def visit3(self, w, p):
        p.login(expect_new=False)
        order = p.api.ok("GET", f"/order/orders/{self.order_id}", "주문")
        check(order["draft_approved"] is True and order["status"] == "IN_PROGRESS", "자동 컨펌돼 게시 단계")
        p.api.expect("POST", f"/order/orders/{self.order_id}/submit-draft", 409, "컨펌 뒤 초안 재제출 불가")
        deliver_and_submit(p, self.order_id, "https://youtu.be/unboxing-final")


class C21(Scenario):
    key, name, account_type = "c21", "배파일", "CREATOR"
    story = "파일로 납품하는 크리에이터 · 엉뚱한 파일은 막히고, 정산은 세 번에 나눠 인출(하나는 계좌 오류)"

    def visit1(self, w, p):
        p.login()
        onboard(p, "푸드", "푸드 스타일링 사진", "서울", [("UGC", "제품 사진 10컷(원본 파일)", 200_000, 2)], [("INSTAGRAM", 7_000, 70)])
        w.expect_review[p.slug] = "APPROVED"
        status, _ = p.api.call("POST", "/creator/my/portfolio", files={"file": ("notes.txt", b"hello", "text/plain")})
        check(status in (400, 415, 422), "포트폴리오에 텍스트 파일 거부", str(status))

    def visit2(self, w, p):
        p.login(expect_new=False)
        for o in p.api.ok("GET", "/order/orders", "주문"):
            if o["status"] != "PENDING_ACCEPT":
                continue
            p.api.ok("POST", f"/order/orders/{o['id']}/accept", f"{o['counterpart_name']} 수락")
            status, _ = p.api.call("POST", f"/order/orders/{o['id']}/deliverables/files", files={"file": ("raw.txt", b"not an image", "text/plain")})
            check(status in (400, 415, 422), "납품 파일 형식 검사", str(status))
            p.api.ok("POST", f"/order/orders/{o['id']}/deliverables/files", "원본 PNG 납품", expect=201,
                     files={"file": ("shot.png", png_bytes(color=(10, 200, 90)), "image/png")})
            p.api.ok("POST", f"/order/orders/{o['id']}/submit", "제출")

    def visit3(self, w, p):
        p.login(expect_new=False)
        amount = balance(p)
        must(amount > 0, "정산 적립")
        p.api.expect("POST", "/order/withdrawals", 422, "0원 인출", json_body={"amount_krw": 0, "bank_name": "국민", "account_number": "1", "account_holder": p.name})
        third = amount // 3
        for i, account in enumerate(("110-222-333333", "0000-0000-0000", "110-222-333333")):
            left = amount - third * 2 if i == 2 else third
            p.api.ok("POST", "/order/withdrawals", f"인출 {i + 1}/3 ({left:,}원, 계좌 {account})", expect=201,
                     json_body={"amount_krw": left, "bank_name": "신한은행", "account_number": account, "account_holder": p.name})
        check(balance(p) == 0, "세 번 나눠 전액 인출 요청")
        w.expect_withdrawal_fail.add(p.user_id)


class C22(Scenario):
    key, name, account_type = "c22", "남정당", "CREATOR"
    story = "일을 다 했는데 브랜드가 사라진 크리에이터 · 직접 분쟁을 걸어 지급 판정을 받는다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "뷰티", "향수 리뷰", "서울", [("INSTAGRAM", "향수 릴스 1건", 160_000, 2)], [("INSTAGRAM", 13_000, 42)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        order = next(o for o in p.api.ok("GET", "/order/orders", "주문") if o["status"] == "PENDING_ACCEPT")
        p.api.ok("POST", f"/order/orders/{order['id']}/accept", "수락")
        deliver_and_submit(p, order["id"], "https://www.instagram.com/reel/perfume/")
        self.order_id = order["id"]

    def visit3(self, w, p):
        p.login(expect_new=False)
        order = p.api.ok("GET", f"/order/orders/{self.order_id}", "주문")
        check(order["status"] == "IN_REVIEW", "브랜드 무응답 — 아직 검토 중", order["status"])
        p.api.ok("POST", f"/order/orders/{self.order_id}/disputes", "지급 요청 분쟁", expect=201,
                 json_body={"reason": "결과물을 제출했는데 브랜드가 응답하지 않습니다. 지급을 요청합니다."})
        w.expect_dispute[self.order_id] = "RELEASE"


class C23(Scenario):
    key, name, account_type = "c23", "이재가입", "BRAND"
    story = "브랜드로 잘못 가입한 크리에이터 · 탈퇴하고 크리에이터로 재가입, 슬러그를 다시 잡는다"

    def visit1(self, w, p):
        p.login()
        p.api.expect("POST", "/creator/profiles", 403, "브랜드 계정으로 프로필 등록 시도",
                     json_body={"slug": p.slug, "name": p.name, "tagline": "x", "bio": "x", "primary_category": "뷰티"})
        p.api.ok("POST", "/auth/account/delete", "잘못 가입해서 탈퇴", expect=204, json_body={"refresh_token": p.refresh_token})

    def visit2(self, w, p):
        p.account_type = "CREATOR"
        p.login(expect_new=True)
        onboard(p, "뷰티", "헤어 스타일링", "광주", [("INSTAGRAM", "헤어 릴스", 140_000, 2)], [("INSTAGRAM", 6_000, 50)])
        w.expect_review[p.slug] = "APPROVED"
        old_slug = p.slug
        p.api.ok("POST", "/auth/account/delete", "프로필까지 만들고 또 탈퇴(주문·잔액 없음)", expect=204, json_body={"refresh_token": p.refresh_token})
        Client(w.http).expect("GET", f"/creator/profiles/{old_slug}", 404, "탈퇴 후 프로필 비노출")
        w.expect_review.pop(p.slug, None)
        p.login(expect_new=True)
        status, payload = p.api.call("POST", "/creator/profiles", json_body={"slug": old_slug, "name": p.name, "tagline": "헤어", "bio": "다시 왔습니다.", "primary_category": "뷰티"})
        if status == 201:
            note("탈퇴로 비활성된 프로필의 슬러그를 새 계정이 바로 재사용할 수 있다")
            p.slug = old_slug
        else:
            note(f"탈퇴한 계정의 슬러그는 회수되지 않는다(재등록 {status}) — 새 슬러그로 등록")
            p.slug = old_slug + "-v2"
            p.api.ok("POST", "/creator/profiles", "새 슬러그로 등록", expect=201,
                     json_body={"slug": p.slug, "name": p.name, "tagline": "헤어", "bio": "다시 왔습니다.", "primary_category": "뷰티"})
        p.api.ok("POST", "/creator/my/analytics", "지표", expect=201, files={"file": ("h.png", png_bytes(), "image/png")},
                 data={"platform": "INSTAGRAM", "followers_count": "6000", "engagement_permille": "50"})
        w.expect_review[p.slug] = "APPROVED"

    def visit3(self, w, p):
        p.login(expect_new=False)
        mine = p.api.ok("GET", "/creator/my/profile", "세 번째 계정의 프로필")
        check(mine["status"] == "APPROVED", "마침내 승인", mine["status"])


class C25(Scenario):
    key, name, account_type = "c25", "구오퍼", "CREATOR"
    story = "오퍼를 남발하는 크리에이터 · 잘못된 오퍼는 막히고, 셋 중 하나만 팔린다"

    def visit1(self, w, p):
        p.login()
        onboard(p, "뷰티", "네일 아트", "서울", [("INSTAGRAM", "네일 릴스", 110_000, 2)], [("INSTAGRAM", 8_500, 65)])
        w.expect_review[p.slug] = "APPROVED"

    def visit2(self, w, p):
        p.login(expect_new=False)
        conv = next(c for c in p.api.ok("GET", "/chat/conversations", "대화") if c["counterpart_name"] == w.people["b13"].name)
        p.api.expect("POST", f"/chat/conversations/{conv['id']}/offers", 422, "0원 오퍼", json_body={"title": "공짜", "price_krw": 0})
        p.api.expect("POST", f"/chat/conversations/{conv['id']}/offers", 422, "제목 101자 오퍼", json_body={"title": "가" * 101, "price_krw": 1000})
        for title, price in (("릴스 2건 묶음", 200_000), ("릴스 2건 + 스토리 3건", 260_000), ("릴스 1건 급행", 150_000)):
            p.api.ok("POST", f"/chat/conversations/{conv['id']}/offers", f"오퍼 '{title}'", expect=201, json_body={"title": title, "price_krw": price, "revision_limit": 1})
        self.conv_id = conv["id"]

    def visit3(self, w, p):
        p.login(expect_new=False)
        offers = p.api.ok("GET", f"/chat/conversations/{self.conv_id}/offers", "오퍼 상태")
        paid = [o for o in offers if o["status"] == "PAID"]
        check(len(paid) == 1 and paid[0]["price_krw"] == 150_000, "가장 싼 급행 오퍼가 팔림")
        p.api.ok("POST", f"/order/orders/{paid[0]['order_id']}/accept", "오퍼 주문 수락")


# ─────────────────────────────── 운영자 5명 ───────────────────────────────


class Admin(Scenario):
    account_type = "CREATOR"

    def setup(self, w: World, p: Person) -> None:
        p.login()
        run_script("auth_grant_role.py", p.email, "admin")
        p.login(expect_new=False)


class A1(Admin):
    key, name = "a1", "박심사"
    story = "프로필 심사 담당 · 지표 재검토 표시가 남은 프로필은 반려, 검증 통과는 승인, 지표 없으면 반려"

    def process(self, w, p, round_no):
        p.login(expect_new=False)
        flagged = {f["profile_slug"] for f in p.api.ok("GET", "/admin/analytics/flagged", "재검토 표시 목록")}
        pending = p.api.ok("GET", "/admin/profiles/pending", f"{round_no}라운드 심사 대기")
        for row in pending:
            if row["slug"] in flagged:
                result = p.api.ok("POST", f"/admin/profiles/{row['id']}/reject", f"{row['name']} 반려(지표 이상치)", json_body={"reason": "자가 입력 지표가 스크린샷과 맞지 않습니다."})
            elif row["vetting_passed"]:
                result = p.api.ok("POST", f"/admin/profiles/{row['id']}/approve", f"{row['name']} 승인")
            else:
                result = p.api.ok("POST", f"/admin/profiles/{row['id']}/reject", f"{row['name']} 반려(지표 없음)", json_body={"reason": "채널 지표 스크린샷이 없습니다."})
            expected = w.expect_review.get(row["slug"])
            if expected:
                check(result["status"] == expected, f"{row['name']} 심사 결과 = 크리에이터 기대({expected})", result["status"])
        missing = set(w.expect_review) - {r["slug"] for r in pending}
        check(not missing, "심사를 기다린다고 선언한 프로필이 모두 대기열에 있었음", str(missing))
        w.expect_review.clear()
        check(p.api.ok("GET", "/admin/profiles/pending", "처리 후 대기열") == [], "대기열 비움")


class A2(Admin):
    key, name = "a2", "이중재"
    story = "분쟁·신고 담당 · 사유에 '지급'이면 크리에이터 지급, '환불'이면 브랜드 환불, 아니면 기각"

    def process(self, w, p, round_no):
        p.login(expect_new=False)
        for d in p.api.ok("GET", "/admin/disputes/open", f"{round_no}라운드 미결 분쟁"):
            if "지급" in d["reason"]:
                action = "release"
            elif "환불" in d["reason"]:
                action = "refund"
            else:
                action = "dismiss"
            verdict = p.api.ok("POST", f"/admin/disputes/{d['id']}/{action}", f"분쟁 #{d['id']} {action} ({d['reason'][:20]}…)")
            expected = w.expect_dispute.pop(d["order_id"], None)
            if expected:
                check(verdict["resolution"] == expected, f"판정 = 당사자 기대({expected})", str(verdict["resolution"]))
            after = next(o for o in p.api.ok("GET", "/admin/orders", "주문 검색", params={"order_id": d["order_id"]})["items"])
            expected_status = {"release": "COMPLETED", "refund": "CANCELLED", "dismiss": d["order_status"]}[action]
            check(after["status"] == expected_status, f"판정 후 주문 상태 {expected_status}", after["status"])
        for r in p.api.ok("GET", "/admin/reports/open", "미처리 신고"):
            resolved = p.api.ok("POST", f"/admin/reports/{r['id']}/resolve", f"신고 #{r['id']} {r['target_type']} 처리", json_body={"note": "확인 결과 조치 불필요" if r["target_type"] == "PROFILE" else "대화방 경고 조치"})
            check(resolved["status"] == "RESOLVED", "RESOLVED")
        check(p.api.ok("GET", "/admin/disputes/open", "잔여 분쟁") == [] and p.api.ok("GET", "/admin/reports/open", "잔여 신고") == [], "분쟁·신고 대기열 비움")


class A3(Admin):
    key, name = "a3", "정정산"
    story = "정산 담당 · 인출 요청을 지급하되 계좌번호가 0000이면 이체 실패 처리해 잔액을 돌려준다"

    def process(self, w, p, round_no):
        p.login(expect_new=False)
        for wd in p.api.ok("GET", "/admin/withdrawals/pending", f"{round_no}라운드 인출 대기"):
            if wd["account_number"].startswith("0000"):
                creator = next(x for x in w.people.values() if x.user_id == wd["creator_user_id"])
                before = balance(creator)
                failed = p.api.ok("POST", f"/admin/withdrawals/{wd['id']}/fail", f"인출 #{wd['id']} 이체 실패(계좌 오류)")
                check(failed["status"] == "FAILED", "FAILED", failed["status"])
                check(balance(creator) - before == wd["amount_krw"], "실패분 잔액 복원")
                w.expect_withdrawal_fail.discard(wd["creator_user_id"])
            else:
                paid = p.api.ok("POST", f"/admin/withdrawals/{wd['id']}/complete", f"인출 #{wd['id']} 지급 {wd['payout_krw']:,}원")
                check(paid["status"] == "PAID", "PAID", paid["status"])
        if round_no == 3:
            summary = p.api.ok("GET", f"/admin/withdrawals/annual-summary/{YEAR}", "연간 지급 요약")
            check(all(s["total_payout_krw"] == s["total_amount_krw"] - s["total_tax_krw"] for s in summary), "요약: 지급 = 인출 − 세금")
            check(not w.expect_withdrawal_fail, "계좌 오류 인출은 모두 실패 처리됨")


class A4(Admin):
    key, name = "a4", "지지표"
    story = "지표 재검토 담당 · '팔로워 급증'은 스크린샷 대조 후 해제, 참여율 이상치는 그대로 두어 심사에서 걸러지게"

    def process(self, w, p, round_no):
        p.login(expect_new=False)
        for f in p.api.ok("GET", "/admin/analytics/flagged", f"{round_no}라운드 재검토 목록"):
            expected = w.expect_flag.get(f["profile_slug"])
            if f["flag_reason"].startswith("팔로워 급증"):
                p.api.ok("POST", f"/admin/analytics/{f['id']}/clear-flag", f"{f['profile_name']} 급증 확인 → 해제", expect=204)
                if expected:
                    check(expected == "CLEAR", f"{f['profile_name']} 처리 = 기대", expected)
            else:
                if expected:
                    check(expected == "KEEP", f"{f['profile_name']} 참여율 이상치 유지 = 기대", expected)
            w.expect_flag.pop(f["profile_slug"], None)
        remaining = p.api.ok("GET", "/admin/analytics/flagged", "처리 후 목록")
        check(all(not r["flag_reason"].startswith("팔로워 급증") for r in remaining), "급증 표시는 모두 해제됨")


class A5(Admin):
    key, name = "a5", "감사감"
    story = "운영 지표·주문 검색·감사 로그를 대조하는 감사 담당 · 운영자 권한이 고객 행동까지 열지는 않는다"

    def process(self, w, p, round_no):
        p.login(expect_new=False)
        metrics = p.api.ok("GET", "/admin/dashboard/metrics", f"{round_no}라운드 운영 지표")
        check(metrics["open_disputes"] == len(p.api.ok("GET", "/admin/disputes/open", "분쟁")), "지표 open_disputes = 목록 수")
        check(metrics["pending_withdrawals"] == len(p.api.ok("GET", "/admin/withdrawals/pending", "인출")), "지표 pending_withdrawals = 목록 수")
        check(metrics["pending_review"] == len(p.api.ok("GET", "/admin/profiles/pending", "심사")), "지표 pending_review = 목록 수")
        for status in ("PENDING_ACCEPT", "IN_PROGRESS", "COMPLETED", "REFUNDED", "CANCELLED"):
            result = p.api.ok("GET", "/admin/orders", f"주문 검색 status={status}", params={"status": status, "limit": 50})
            check(all(o["status"] == status for o in result["items"]), f"{status} 검색 결과 일치")
        if round_no >= 2:
            b10 = w.people["b10"]
            result = p.api.ok("GET", "/admin/orders", "b10 참여 주문", params={"user_id": b10.user_id})
            check(result["total"] == 3, "b10 주문 3건", str(result["total"]))
        if round_no == 3:
            stuck = [o for o in p.api.ok("GET", "/admin/orders", "취소 요청 대기 주문", params={"limit": 50})["items"] if o["cancel_requested_by"]]
            check(len(stuck) >= 1, "취소 요청 대기 주문 파악(c07)", str(len(stuck)))
            logs = p.api.ok("GET", "/admin/audit-logs", "감사 로그")
            check(any("승인" in l["note"] for l in logs) and any("지급" in l["note"] for l in logs), "심사·정산 감사 로그 존재")
        p.api.expect("POST", "/payment/checkouts", 403, "운영자 계정(크리에이터 유형)은 주문 불가", json_body={"package_id": 1, "requirements": "x"})
        p.api.expect("POST", "/campaign/campaigns", 403, "운영자 계정은 공고 불가", json_body={"title": "x", "description": "x", "platform": "INSTAGRAM", "budget_krw": 1})


# ─────────────────────────────── 조립·실행 ───────────────────────────────

BRANDS = [B01, B02, B03, B04, B05, B06, B07, B08, B09, B10, B11, B12, B13, B14]
CREATORS = [C01, C02, C03, C04, C06, C07, C08, C10, C11, C16, C18, C19, C21, C22, C23, C25]
ADMINS = [A4, A1, A2, A3, A5]  # 지표 재검토가 심사보다 먼저 — 심사가 그 결과를 본다


class CohortWorld(World):
    def __init__(self, http):
        super().__init__(http)
        self.scenarios: dict[str, Scenario] = {}
        self.expect_review: dict[str, str] = {}  # slug → 크리에이터가 기대하는 심사 결과
        self.expect_flag: dict[str, str] = {}  # slug → CLEAR/KEEP
        self.expect_dispute: dict[int, str] = {}  # order_id → RELEASE/REFUND/DISMISS
        self.expect_withdrawal_fail: set[int] = set()


def run_visit(w: CohortWorld, scenario: Scenario, round_no: int, stopped: set[str]) -> None:
    fn = getattr(type(scenario), f"visit{round_no}", None)
    if fn is None or fn is getattr(Scenario, f"visit{round_no}") or scenario.key in stopped:
        return
    p = w.people[scenario.key]
    base._current[0] = f"{scenario.name}({scenario.key})"
    print(f"\n  [{scenario.key} · {scenario.name}] 방문 {round_no}")
    try:
        fn(scenario, w, p)
    except StepFailed as stop:
        print(f"    ⛔ 여정 중단: {stop}")
        stopped.add(scenario.key)
    except Exception:  # noqa: BLE001
        check(False, "예상치 못한 오류", traceback.format_exc().strip().splitlines()[-1])
        traceback.print_exc()
        stopped.add(scenario.key)


def main() -> int:
    parser = argparse.ArgumentParser(description="코호트 여정 회귀 — 고객 30 + 운영자 5, 3회 방문")
    parser.add_argument("--browser", action="store_true", help="마지막에 화면 확인(프론트 :3000)")
    args = parser.parse_args()

    print(f"스텁 백엔드 기동(:{base.PORT})…")
    server = base.start_stub_backend()
    stopped: set[str] = set()
    try:
        with httpx.Client() as http:
            w = CohortWorld(http)
            for cls in BRANDS + CREATORS + ADMINS:
                s = cls()
                w.scenarios[s.key] = s
                w.person(s.key, s.name, s.account_type)
            print("\n[운영자 준비]")
            for cls in ADMINS:
                s = w.scenarios[cls.key]
                base._current[0] = f"{s.name}({s.key})"
                s.setup(w, w.people[s.key])

            for round_no in (1, 2, 3):
                print(f"\n{'=' * 26} 라운드 {round_no} — 고객 {'=' * 26}")
                for cls in BRANDS + CREATORS:
                    run_visit(w, w.scenarios[cls.key], round_no, stopped)
                print(f"\n{'-' * 26} 라운드 {round_no} — 운영자 {'-' * 24}")
                for cls in ADMINS:
                    s = w.scenarios[cls.key]
                    base._current[0] = f"{s.name}({s.key})"
                    print(f"\n  [{s.key} · {s.name}] {s.story}")
                    try:
                        s.process(w, w.people[s.key], round_no)
                    except StepFailed as stop:
                        print(f"    ⛔ 처리 중단: {stop}")
                    except Exception:  # noqa: BLE001
                        check(False, "예상치 못한 오류", traceback.format_exc().strip().splitlines()[-1])
                        traceback.print_exc()
                relay_notifications()

            base.check_integrity()
            if args.browser:
                targets = [
                    ("b01", f"/dashboard/orders/{latest_order(w.people['b01'], w.people['c01'])['id']}", "인스타 피드 1건"),
                    ("c02", "/dashboard/profile", "허과장"),
                    ("b07", f"/campaigns/{w.scenarios['b07'].main['id']}", "가계부 앱"),
                    ("b13", f"/chat/{w.scenarios['b13'].conv2}", "릴스"),
                    ("c21", "/dashboard/balance", "인출"),
                    ("a5", "/admin", "운영 콘솔"),
                ]
                base.browser_checks(w, targets)
    finally:
        server.terminate()
        server.wait(timeout=10)

    failures = [(who, label) for ok, who, label in base._results if not ok]
    print("\n" + "=" * 70)
    for who, label in failures:
        print(f"  ✕ [{who}] {label}")
    for who, text in base._notes:
        print(f"  ⓘ [{who}] {text}")
    if stopped:
        print(f"  ⛔ 중단된 페르소나: {', '.join(sorted(stopped))}")
    print(f"통과 {len(base._results) - len(failures)} · 실패 {len(failures)} · 관찰 {len(base._notes)} · 실행 접미사 {base.RUN}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
