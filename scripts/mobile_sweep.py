#!/usr/bin/env python3
"""모바일(375px) 전 라우트 가로 넘침 스캔 (갭 #92) — e2e.py를 보완하는 반응형 회귀 도구.

e2e.py는 기능 동작을 보고, 이 스크립트는 **화면이 뷰포트를 넘어 가로 스크롤이 생기는지**를
전 라우트에 대해 검사한다. 넘침이 있으면 원인 요소(뷰포트보다 넓은 가장 바깥 요소)를 찍고
스크린샷을 남긴다. 2026-08-18 전수 점검 기준 36개 라우트 전부 넘침 0건.

실행(백엔드·프론트 기동 뒤):
    .venv/bin/python scripts/mobile_sweep.py               # 375px(기본)
    .venv/bin/python scripts/mobile_sweep.py --width 320   # 더 좁은 폭 점검

사전 조건: docker compose up -d · 백엔드 · 프론트(:3000) · seed_demo_data 계정/데모 데이터.
새 라우트를 추가하면 아래 목록에도 등록한다(동적 라우트는 데모 데이터의 대표 1건).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = "http://localhost:3000"

PUBLIC_ROUTES = [
    "/", "/creators/haneul-beauty", "/creators/doyun-tech", "/creators/category/뷰티",
    "/campaigns", "/cart", "/shortlist", "/login",
    "/blog", "/blog/how-to-price-your-content", "/faq", "/how-it-works",
    "/for/marketing-teams", "/for/founders", "/for/creators",
    "/terms", "/privacy",
    "/tools", "/tools/pricing-calculator", "/tools/engagement-calculator",
    "/tools/campaign-brief", "/tools/contract-template",
]
# (계정, 라우트 목록) — 로그인 필요 화면. 주문 8·캠페인 4 등은 seed·검증 데이터의 대표 건.
AUTH_ROUTES = [
    ("jang971121@gmail.com", ["/admin", "/notifications"]),
    ("jang037@naver.com", ["/dashboard/orders", "/dashboard/campaigns", "/campaigns/4", "/chat"]),
    ("demo-brand@crecity.kr", ["/dashboard/orders/8", "/dashboard/orders/8/contract", "/dashboard/balance"]),
    ("demo-haneul-beauty@crecity.kr", [
        "/dashboard/profile", "/dashboard/packages", "/dashboard/balance",
        "/dashboard/orders/9", "/dashboard/settings",
    ]),
]

# 넘침이면 (문서 폭, 뷰포트 폭, 원인 요소 목록)을 돌려준다 — 원인은 가장 바깥 요소만
OVERFLOW_JS = """() => {
  const doc = document.documentElement;
  if (doc.scrollWidth <= doc.clientWidth) return null;
  const wide = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width > doc.clientWidth + 1 || r.right > doc.clientWidth + 1 || r.left < -1) {
      if (!wide.some((w) => w.el.contains(el))) wide.push({ el, r });
    }
    if (wide.length >= 5) break;
  }
  return {
    scrollWidth: doc.scrollWidth,
    clientWidth: doc.clientWidth,
    causes: wide.map(({ el, r }) =>
      `${el.tagName.toLowerCase()}.${String(el.className).slice(0, 80)} w=${Math.round(r.width)} l=${Math.round(r.left)} r=${Math.round(r.right)}`),
  };
}"""

_results: list[tuple[bool, str, str]] = []
_shot_dir = Path(tempfile.gettempdir()) / "crecity-mobile-sweep"


def issue_refresh(email: str) -> str | None:
    result = subprocess.run(
        [str(ROOT / ".venv/bin/python"), "scripts/dev_issue_refresh.py", email],
        cwd=ROOT / "crecity",
        env={"PYTHONPATH": ".:apps", "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    lines = [line for line in result.stdout.splitlines() if line]
    return lines[-1] if lines else None


def scan(page, route: str, label: str) -> None:
    try:
        page.goto(f"{FRONTEND}{route}", timeout=45_000)
        page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception as error:
        _results.append((False, label, f"로드 실패: {str(error)[:80]}"))
        print(f"  ✗ {label} — 로드 실패")
        return
    page.wait_for_timeout(500)
    overflow = page.evaluate(OVERFLOW_JS)
    if overflow is None:
        _results.append((True, label, ""))
        print(f"  ✓ {label}")
        return
    detail = f"{overflow['scrollWidth']}>{overflow['clientWidth']} — " + "; ".join(overflow["causes"][:3])
    _results.append((False, label, detail))
    _shot_dir.mkdir(exist_ok=True)
    shot = _shot_dir / f"{label.strip('/').replace('/', '_').replace(':', '_') or 'home'}.png"
    page.screenshot(path=str(shot), full_page=True)
    print(f"  ✗ {label} — {detail} → {shot}")


def main() -> int:
    parser = argparse.ArgumentParser(description="모바일 가로 넘침 스캔")
    parser.add_argument("--width", type=int, default=375, help="뷰포트 폭(기본 375)")
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        print("[공개 화면]")
        ctx = browser.new_context(viewport={"width": args.width, "height": 812})
        page = ctx.new_page()
        for route in PUBLIC_ROUTES:
            scan(page, route, route)
        ctx.close()

        for email, routes in AUTH_ROUTES:
            name = email.split("@")[0]
            print(f"[{name}]")
            token = issue_refresh(email)
            if not token:
                _results.append((False, name, "리프레시 토큰 발급 실패"))
                continue
            ctx = browser.new_context(viewport={"width": args.width, "height": 812})
            ctx.add_cookies([{
                "name": "crecity_refresh", "value": token, "domain": "localhost",
                "path": "/api/auth", "httpOnly": True, "sameSite": "Lax",
            }])
            page = ctx.new_page()
            for route in routes:
                scan(page, route, f"{name}:{route}")
            ctx.close()
        browser.close()

    failed = [(label, detail) for ok, label, detail in _results if not ok]
    print(f"\n검사 {len(_results)} · 넘침/실패 {len(failed)}")
    for label, detail in failed:
        print(f"실패: {label} — {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
