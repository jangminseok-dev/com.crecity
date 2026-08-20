#!/usr/bin/env python3
"""실행 중인 서버에 대고 도는 스모크 회귀 — 손으로 치던 curl 묶음을 한 줄로.

pytest는 유스케이스를 스텁으로 검증하고, 이 스크립트는 **실제로 뜬 서버와 DB**를 본다.
둘은 겹치지 않는다 — 라우터 조립·권한 게이트·응답 필드·데이터 정합성은 여기서만 잡힌다
(실제로 `GET /creator/my/profile`의 필드 누락은 pytest·typecheck 둘 다 통과했었다).

실행:
    .venv/bin/python scripts/smoke.py              # 백엔드만
    .venv/bin/python scripts/smoke.py --frontend   # 프론트 라우트까지
    .venv/bin/python scripts/smoke.py --no-auth    # 토큰 발급 없이(서버만 확인)

사전 조건: docker compose up -d · 백엔드(:8000) 기동. --frontend면 프론트(:3000)도.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 8000이 다른 프로세스(VS Code 포트 포워딩 등)에 점유됐을 때 SMOKE_BACKEND로 우회한다
BACKEND = os.environ.get("SMOKE_BACKEND", "http://127.0.0.1:8000")
FRONTEND = "http://127.0.0.1:3000"

# 토큰을 발급할 계정 — seed_demo_data.py가 만드는 계정과 실제 개발 계정
ADMIN_EMAIL = "jang971121@gmail.com"
BRAND_EMAIL = "jang037@naver.com"
CREATOR_EMAIL = "kim-beauty@sample.crecity.local"

_results: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    _results.append((ok, f"{label}{f' — {detail}' if detail else ''}"))
    return ok


def request(url: str, token: str | None = None, method: str = "GET", body: dict | None = None):
    """(상태코드, 파싱된 JSON 또는 None) — 네트워크 실패는 상태코드 0."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            try:
                return response.status, json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # HTML·이미지 등 JSON이 아닌 응답 — 상태코드만 본다
                return response.status, None
    except urllib.error.HTTPError as error:
        return error.code, None
    except OSError:
        return 0, None


def expect(url: str, status: int, label: str, token: str | None = None) -> None:
    actual, _ = request(url, token)
    check(actual == status, label, f"기대 {status} / 실제 {actual}")


def issue_token(email: str) -> str | None:
    """dev_issue_token.py를 그대로 부른다 — 발급 로직을 두 벌로 만들지 않는다."""
    result = subprocess.run(
        [str(ROOT / ".venv/bin/python"), "scripts/dev_issue_token.py", email],
        cwd=ROOT / "crecity",
        env={"PYTHONPATH": ".:apps", "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    lines = [line for line in result.stdout.splitlines() if line and not line.startswith("#")]
    return lines[-1] if lines else None


def check_public() -> None:
    print("\n[공개 API]")
    for path in (
        "/creator/profiles",
        "/creator/profiles?sort=price_asc",
        "/creator/profiles?followers_min=1000&engagement_min=10",
        "/creator/categories",
        "/creator/profiles/popular?limit=4",
        "/creator/profiles/minseok-studio/similar",
        "/creator/market-rates",
        "/order/fee-policy",
    ):
        expect(f"{BACKEND}{path}", 200, f"GET {path}")
    expect(f"{BACKEND}/creator/profiles?sort=bogus", 422, "잘못된 정렬값 거부")
    expect(f"{BACKEND}/creator/profiles/no-such-slug", 404, "없는 프로필 404")
    for app in ("creator", "order", "review", "campaign", "chat", "notification", "payment", "admin", "auth", "hub"):
        expect(f"{BACKEND}/{app}/myself", 200, f"{app} 자기소개")


def check_auth_required() -> None:
    print("\n[인증 게이트]")
    for path in (
        "/creator/my/profile",
        "/order/orders",
        "/order/balance",
        "/order/reports/2026",
        "/admin/dashboard/metrics",
        "/admin/reports/open",
        "/admin/orders",
    ):
        expect(f"{BACKEND}{path}", 401, f"미인증 차단 {path}")


def check_with_tokens() -> None:
    print("\n[토큰 경로]")
    admin = issue_token(ADMIN_EMAIL)
    creator = issue_token(CREATOR_EMAIL)
    brand = issue_token(BRAND_EMAIL)
    if not check(bool(admin and creator and brand), "토큰 발급"):
        return

    for path in (
        "/admin/dashboard/metrics",
        "/admin/orders",
        "/admin/reports/open",
        "/admin/reports/resolved",
        "/admin/disputes/open",
        "/admin/disputes/resolved",
        "/admin/audit-logs",
        "/admin/profiles/pending",
    ):
        expect(f"{BACKEND}{path}", 200, f"운영자 {path}", token=admin)

    # 권한 없는 계정은 운영 API에 닿지 못한다
    expect(f"{BACKEND}/admin/reports/open", 403, "권한 없는 운영 API 차단", token=brand)

    # 응답 필드 — 화면이 읽는 값이 실제로 오는지(타입 검사로는 못 잡는 부분)
    status, profile = request(f"{BACKEND}/creator/my/profile", creator)
    check(status == 200 and profile is not None, "내 프로필 조회")
    if profile:
        check("accepting_orders" in profile, "내 프로필에 accepting_orders 포함")
    status, views = request(f"{BACKEND}/creator/my/profile/views", creator)
    check(
        status == 200 and views is not None and len(views.get("daily", [])) == views.get("days"),
        "조회수 추이 일수 일치",
    )
    status, orders = request(f"{BACKEND}/order/orders", brand)
    check(status == 200 and orders is not None, "브랜드 주문 목록")
    if orders:
        first = orders[0]
        check(
            "counterpart_name" in first and "counterpart_completed_orders" in first,
            "주문에 거래 상대·이력 포함",
        )


def check_data_integrity() -> None:
    print("\n[데이터 정합성]")
    result = subprocess.run(
        [str(ROOT / ".venv/bin/python"), "-c", _INTEGRITY_SNIPPET],
        cwd=ROOT / "crecity",
        env={"PYTHONPATH": ".:apps", "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        check(False, "DB 정합성 조회", result.stderr.strip().splitlines()[-1] if result.stderr else "")
        return
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    check(payload["orphan_orders"] == 0, "원장 없는 주문", f"{payload['orphan_orders']}건")
    check(
        payload["fee_from_rate"] == payload["fee_from_ledger"],
        "수수료: 요율 계산 == 원장 합",
        f"{payload['fee_from_rate']:,} vs {payload['fee_from_ledger']:,}",
    )


_INTEGRITY_SNIPPET = """
import asyncio, json
from sqlalchemy import text
from core.database import session_scope

async def main():
    async with session_scope() as s:
        orphan = (await s.execute(text(
            'SELECT count(*) FROM orders o WHERE (SELECT count(*) FROM ledger_entries l WHERE l.order_id=o.id)=0'
        ))).scalar()
        rate = (await s.execute(text(
            "SELECT COALESCE(sum(floor(amount_krw*brand_fee_percent/100.0)"
            " + floor(amount_krw*creator_fee_percent/100.0)),0) FROM orders WHERE status='COMPLETED'"
        ))).scalar()
        ledger = (await s.execute(text(
            "SELECT COALESCE(sum(amount_krw),0) FROM ledger_entries WHERE entry_type='PLATFORM_REVENUE'"
        ))).scalar()
    print(json.dumps({'orphan_orders': int(orphan), 'fee_from_rate': int(rate), 'fee_from_ledger': int(ledger)}))

asyncio.run(main())
"""


def check_frontend() -> None:
    print("\n[프론트 라우트]")
    for path in (
        "/",
        "/?sort=price_asc",
        "/creators/kim-beauty",
        "/creators/category/%EB%B7%B0%ED%8B%B0",
        "/how-it-works",
        "/faq",
        "/terms",
        "/privacy",
        "/tools",
        "/tools/pricing-calculator",
        "/tools/campaign-brief",
        "/tools/contract-template",
        "/blog",
        "/blog/influencer-pricing-guide",
        "/for/marketing-teams",
        "/login",
        "/admin",
        "/dashboard/profile",
        "/robots.txt",
        "/sitemap.xml",
        "/creators/kim-beauty/opengraph-image",
    ):
        expect(f"{FRONTEND}{path}", 200, f"GET {path}")
    expect(f"{FRONTEND}/no-such-page", 404, "없는 주소 404")
    expect(f"{FRONTEND}/creators/no-such-slug", 404, "없는 프로필 404")
    expect(f"{FRONTEND}/blog/no-such-post", 404, "없는 블로그 글 404")


def main() -> int:
    parser = argparse.ArgumentParser(description="실행 중인 서버에 대한 스모크 회귀")
    parser.add_argument("--frontend", action="store_true", help="프론트 라우트도 확인")
    parser.add_argument("--no-auth", action="store_true", help="토큰 발급 없이 실행")
    args = parser.parse_args()

    status, _ = request(f"{BACKEND}/creator/myself")
    if status != 200:
        print(f"백엔드가 응답하지 않습니다({BACKEND}) — 먼저 서버를 띄우세요.", file=sys.stderr)
        return 2

    check_public()
    check_auth_required()
    if not args.no_auth:
        check_with_tokens()
    check_data_integrity()
    if args.frontend:
        status, _ = request(f"{FRONTEND}/")
        if status == 200:
            check_frontend()
        else:
            check(False, "프론트 응답", f"{FRONTEND} 상태 {status}")

    failures = [label for ok, label in _results if not ok]
    for label in failures:
        print(f"  ✕ {label}")
    print(f"\n통과 {len(_results) - len(failures)} · 실패 {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
