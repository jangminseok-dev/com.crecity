#!/usr/bin/env python3
"""브라우저 E2E 화면 회귀 (검증 5층째, 갭 #91) — 로그인 상태의 실제 렌더를 본다.

smoke.py는 HTTP 응답까지만 본다 — "화면이 제대로 그려지는가"는 브라우저에서만 잡힌다.
실제로 2026-08-18 육안 점검에서 리뷰 블러 고정·채팅 스크롤 버그를 찾았고,
이 스크립트는 그 두 건을 회귀 검증으로 못 박는다.

로그인은 실제 경로를 그대로 탄다: dev_issue_refresh.py로 진짜 리프레시 토큰을 만들어
httpOnly 쿠키에 심으면, 앱이 부팅하면서 POST /api/auth/refresh로 세션을 복원한다.

실행:
    .venv/bin/python scripts/e2e.py                # 데스크톱(1280px)
    .venv/bin/python scripts/e2e.py --viewport 375 # 모바일 폭(갭 #92용)

사전 조건: docker compose up -d · 백엔드 · 프론트(:3000) 기동 · seed_demo_data 계정/데모 데이터.
브라우저는 설치된 Chrome을 쓴다(channel="chrome" — 별도 다운로드 없음).
실패 화면은 임시 디렉토리에 스크린샷으로 남기고 경로를 출력한다.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = "http://localhost:3000"  # 쿠키 도메인(localhost)과 일치해야 한다

# seed_demo_data.py가 만드는 계정 — smoke.py와 동일
ADMIN_EMAIL = "jang971121@gmail.com"  # admin 역할 + 크리에이터(민석, 리뷰 보유)
BRAND_EMAIL = "jang037@naver.com"
CREATOR_EMAIL = "kim-beauty@sample.crecity.local"
REVIEWED_CREATOR_SLUG = "minseok-studio"  # 리뷰가 있는 프로필 — 답글·블러 회귀 검증용

WAIT_MS = 15_000  # next dev는 라우트를 온디맨드 컴파일한다 — 첫 진입이 느릴 수 있음

_results: list[tuple[bool, str]] = []
_shot_dir = Path(tempfile.gettempdir()) / "crecity-e2e"


def check(ok: bool, label: str, detail: str = "", page: Page | None = None) -> bool:
    _results.append((ok, f"{label}{f' — {detail}' if detail else ''}"))
    if not ok and page is not None:
        _shot_dir.mkdir(exist_ok=True)
        shot = _shot_dir / f"{len(_results):02d}-{label.replace(' ', '_').replace('/', '_')}.png"
        page.screenshot(path=str(shot), full_page=True)
        print(f"  ✗ {label} → {shot}")
    return ok


def see(page: Page, text: str, label: str) -> bool:
    """텍스트가 화면에 나타나는지 — 나타나면 통과."""
    try:
        page.wait_for_selector(f"text={text}", timeout=WAIT_MS)
        return check(True, label)
    except PlaywrightTimeout:
        return check(False, label, f"'{text}' 미표시", page)


def issue_refresh(email: str) -> str | None:
    """dev_issue_refresh.py를 그대로 부른다 — 발급 로직을 두 벌로 만들지 않는다."""
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


def new_logged_in_page(browser, token: str, width: int, problems: list[str]) -> Page:
    context = browser.new_context(viewport={"width": width, "height": 900})
    context.add_cookies(
        [
            {
                "name": "crecity_refresh",
                "value": token,
                "domain": "localhost",
                "path": "/api/auth",
                "httpOnly": True,
                "sameSite": "Lax",
            }
        ]
    )
    page = context.new_page()
    page.on(
        "console",
        lambda msg: problems.append(f"console: {msg.text[:150]}") if msg.type == "error" else None,
    )
    page.on(
        "response",
        lambda res: problems.append(f"{res.status} {res.url[:120]}")
        if res.status >= 400 and "/api/" in res.url
        else None,
    )
    return page


def check_admin(page: Page) -> None:
    print("\n[운영 콘솔 — admin]")
    page.goto(f"{FRONTEND}/admin")
    see(page, "운영 콘솔", "운영 콘솔 진입")
    see(page, "운영 현황", "지표 섹션(기본 탭)")
    # 왼쪽 탭 목록 — 탭을 눌러야 해당 섹션 제목(h2)이 그려진다(2026-09-02 탭 구조 전환)
    for label in ("주문 검색", "감사 로그"):
        page.get_by_role("button", name=label, exact=True).click()
        try:
            page.wait_for_selector(f"h2:has-text('{label}')", timeout=WAIT_MS)
            check(True, f"{label} 탭 전환")
        except PlaywrightTimeout:
            check(False, f"{label} 탭 전환", "섹션 제목 미표시", page)
    check("tab=audit" in page.url, "탭이 URL(?tab=)에 유지", page.url)

    # 회귀: 리뷰 블러 고정 — 로그인 상태로 프로필 직접 진입 시 원문·답글 UI가 보여야 한다
    # (세션 복원 전 공개 API 조회가 게스트 응답으로 캐시되던 버그, 2026-08-18 수정)
    print("\n[리뷰 원문·답글 — 본인 프로필 직접 진입]")
    page.goto(f"{FRONTEND}/creators/{REVIEWED_CREATOR_SLUG}")
    see(page, "리뷰", "프로필 진입")
    try:
        page.wait_for_selector("text=답글 남기기", timeout=WAIT_MS)
        check(True, "본인 리뷰에 답글 UI 표시")
    except PlaywrightTimeout:
        replied = page.locator("text=크리에이터 답글").count() > 0
        check(replied, "본인 리뷰에 답글 UI 표시", "답글 남기기·크리에이터 답글 모두 없음", page)
    locked = page.locator("text=로그인하고 리뷰 원문 보기").count()
    check(locked == 0, "로그인 상태에서 리뷰 원문 잠금 해제", f"잠긴 리뷰 {locked}건", page)


def check_brand(page: Page) -> None:
    print("\n[브랜드 — 주문·계약·채팅·알림]")
    page.goto(f"{FRONTEND}/dashboard/orders")
    see(page, "브랜드 대시보드", "브랜드 대시보드 진입")
    page.wait_for_selector('a[href^="/dashboard/orders/"]', timeout=WAIT_MS)
    hrefs = [
        link.get_attribute("href")
        for link in page.locator('a[href^="/dashboard/orders/"]').all()
    ]
    check(len(hrefs) > 0, "주문 목록 행 표시", f"{len(hrefs)}건")

    # 계약 조건 확인서(#52) — 확인서 링크가 있는 주문을 찾을 때까지 앞에서부터 연다
    contract_found = False
    for href in hrefs[:5]:
        page.goto(f"{FRONTEND}{href}")
        page.wait_for_selector("text=패키지", timeout=WAIT_MS)
        if page.locator("text=조건 확인서 보기").count() > 0:
            page.click("text=조건 확인서 보기")
            contract_found = see(page, "주문 계약 조건 확인서", "계약 조건 확인서 렌더")
            break
    if not contract_found:
        check(False, "계약 조건 확인서 렌더", "확인서 링크가 있는 주문을 찾지 못함", page)

    # 회귀: 채팅 스크롤 — 진입 시 window가 밀리지 않아야 한다(2026-08-18 수정)
    page.goto(f"{FRONTEND}/chat")
    see(page, "메시지", "채팅 목록 진입")
    page.wait_for_selector('main a[href^="/chat/"]', timeout=WAIT_MS)
    page.locator('main a[href^="/chat/"]').first.click()
    page.wait_for_selector('input[placeholder="메시지를 입력하세요"]', timeout=WAIT_MS)
    page.wait_for_timeout(1_500)  # 메시지 로드 → 스크롤 이펙트 여유
    scroll_y = page.evaluate("window.scrollY")
    check(scroll_y == 0, "채팅방 진입 시 window 스크롤 고정", f"scrollY={scroll_y}", page)
    header_visible = page.locator("main h1").first.is_visible()
    check(header_visible, "채팅 상대 정보 표시", page=page)

    page.goto(f"{FRONTEND}/notifications")
    see(page, "알림", "알림 목록 진입")


def check_creator(page: Page) -> None:
    print("\n[크리에이터 — 대시보드]")
    page.goto(f"{FRONTEND}/dashboard/profile")
    see(page, "프로필 완성도", "온보딩 체크리스트 표시")
    toggle = (
        page.locator("text=주문을 받는 중").count() + page.locator("text=주문 잠시 중단").count()
    )
    check(toggle > 0, "주문 수신 토글 표시", page=page)

    page.goto(f"{FRONTEND}/dashboard/balance")
    see(page, "인출 요청", "인출 폼 표시")
    see(page, "지급명세서", "지급명세서 섹션 표시")

    # 내 지원 내역(갭 #103) — 같은 URL이 브랜드에겐 공고 등록 폼이다(계정 유형 분기)
    see(page, "내 지원", "크리에이터 탭에 내 지원 노출")
    page.goto(f"{FRONTEND}/dashboard/campaigns")
    # 지원 상태 배지 또는 빈 안내 — 조회가 끝날 때까지 기다린 뒤 본다(즉시 count는 스켈레톤을 센다)
    see(page, "/검토 대기|미선정|선정|아직 지원한 공고가 없습니다/", "지원 내역 상태 또는 빈 안내 표시")
    check(
        page.locator("text=공고 등록").count() == 0,
        "크리에이터 화면에 브랜드 공고 폼 없음",
        page=page,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="브라우저 E2E 화면 회귀")
    parser.add_argument("--viewport", type=int, default=1280, help="뷰포트 폭(기본 1280)")
    args = parser.parse_args()

    try:
        with urllib.request.urlopen(FRONTEND, timeout=5) as response:
            assert response.status == 200
    except OSError:
        print(f"프론트가 응답하지 않습니다({FRONTEND}) — 먼저 서버를 띄우세요.", file=sys.stderr)
        return 2

    tokens = {email: issue_refresh(email) for email in (ADMIN_EMAIL, BRAND_EMAIL, CREATOR_EMAIL)}
    if not all(tokens.values()):
        missing = [email for email, token in tokens.items() if not token]
        print(f"리프레시 토큰 발급 실패: {missing} — DB·Redis와 계정을 확인하세요.", file=sys.stderr)
        return 2

    plans = [
        (ADMIN_EMAIL, check_admin),
        (BRAND_EMAIL, check_brand),
        (CREATOR_EMAIL, check_creator),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for email, run_checks in plans:
            problems: list[str] = []
            page = new_logged_in_page(browser, tokens[email], args.viewport, problems)
            run_checks(page)
            check(not problems, f"{email.split('@')[0]} 콘솔 에러·API 실패 없음",
                  "; ".join(problems[:3]))
            page.context.close()
        browser.close()

    passed = sum(1 for ok, _ in _results if ok)
    failed = [(ok, label) for ok, label in _results if not ok]
    for _, label in failed:
        print(f"실패: {label}")
    print(f"\n통과 {passed} · 실패 {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
