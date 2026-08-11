"""데모 데이터 시드 — 사진·패키지·완료 주문·리뷰가 채워진 크리에이터를 만든다.

화면 완성도 확인·시연용. slug가 이미 있으면 해당 크리에이터는 건너뛴다(재실행 안전).

실행:
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/seed_demo_data.py
"""

from __future__ import annotations

import asyncio
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))

from sqlalchemy import insert  # noqa: E402

from core.database import dispose_engine, init_engine, session_scope  # noqa: E402
from auth.adapter.outbound.pg.user_pg_repository import UserPgRepository  # noqa: E402
from auth.domain.entities.user_entity import AccountType  # noqa: E402
from creator.adapter.outbound.local_portfolio_file_storage import (  # noqa: E402
    LocalPortfolioFileStorage,
)
from creator.adapter.outbound.pg.creator_package_pg_repository import (  # noqa: E402
    CreatorPackagePgRepository,
)
from creator.adapter.outbound.pg.creator_profile_pg_repository import (  # noqa: E402
    CreatorProfilePgRepository,
)
from creator.adapter.outbound.pg.portfolio_item_pg_repository import (  # noqa: E402
    PortfolioItemPgRepository,
)
from creator.domain.entities.creator_package_entity import PackagePlatform  # noqa: E402
from creator.domain.entities.creator_profile_entity import ProfileStatus  # noqa: E402
from order.adapter.outbound.orm.order_orm import OrderOrm  # noqa: E402
from review.adapter.outbound.orm.review_orm import ReviewOrm  # noqa: E402

# (slug, 이름, 카테고리, 지역, 한 줄 소개, 그라데이션 색 2개, 패키지들, 완료 주문 수, 리뷰 점수들)
DEMO_CREATORS = [
    {
        "slug": "haneul-beauty",
        "name": "김하늘",
        "category": "뷰티",
        "location": "서울",
        "tagline": "20대 스킨케어·K뷰티 성분 리뷰",
        "bio": "성분 분석과 실사용 후기를 담백한 톤으로 전달해요.\n브랜드 무드에 맞춘 기획안을 먼저 제안드리고 시작합니다.",
        "colors": ((242, 214, 222), (196, 148, 170)),
        "packages": [
            (PackagePlatform.INSTAGRAM, "인스타그램 릴스 1편", "30초 내외, 기획·촬영·편집, 2회 수정 포함", 350_000),
            (PackagePlatform.INSTAGRAM, "피드 게시물 3장", "제품 연출 컷, 캡션 작성 포함", 250_000),
        ],
        "orders": 3,
        "reviews": [(5, 5, 5), (5, 4, 5), (4, 5, 5)],
    },
    {
        "slug": "doyun-tech",
        "name": "이도윤",
        "category": "테크",
        "location": "판교",
        "tagline": "가성비 전자기기·앱 심층 리뷰",
        "bio": "스펙 비교와 2주 실사용 리뷰로 구매 전환을 만들어요.\n유튜브 구독자 38만, 평균 조회수 12만.",
        "colors": ((205, 219, 242), (140, 165, 210)),
        "packages": [
            (PackagePlatform.YOUTUBE, "유튜브 리뷰 영상 1편", "8분 내외 심층 리뷰, 챕터·자막 포함", 1_200_000),
            (PackagePlatform.YOUTUBE, "쇼츠 3편 패키지", "핵심 기능 하이라이트 60초 쇼츠", 600_000),
        ],
        "orders": 2,
        "reviews": [(5, 5, 4), (4, 4, 5)],
    },
    {
        "slug": "minjun-food",
        "name": "정민준",
        "category": "푸드",
        "location": "부산",
        "tagline": "맛집·간편식 숏폼 전문",
        "bio": "먹는 소리와 클로즈업으로 식욕을 자극하는 틱톡 숏폼을 만듭니다.\n지역 맛집 캠페인 경험 다수.",
        "colors": ((247, 230, 202), (214, 168, 116)),
        "packages": [
            (PackagePlatform.TIKTOK, "틱톡 숏폼 2편", "촬영·편집·해시태그 세팅 포함", 450_000),
            (PackagePlatform.UGC, "UGC 영상 소스 5컷", "광고 소재용 원본 클립 납품", 300_000),
        ],
        "orders": 2,
        "reviews": [(5, 5, 5), (5, 5, 4)],
    },
    {
        "slug": "yuna-travel",
        "name": "최유나",
        "category": "여행",
        "location": "제주",
        "tagline": "감성 여행 브이로그·숙소 리뷰",
        "bio": "숙소·액티비티의 분위기를 살리는 시네마틱 영상이 강점이에요.\n네이버 블로그 동시 발행으로 검색 유입까지 챙깁니다.",
        "colors": ((209, 234, 226), (130, 180, 168)),
        "packages": [
            (PackagePlatform.INSTAGRAM, "여행 릴스 1편", "현장 촬영, 시네마틱 편집", 400_000),
            (PackagePlatform.NAVER_BLOG, "블로그 체험 리뷰", "사진 20장 + 2,000자 상세 리뷰", 200_000),
        ],
        "orders": 1,
        "reviews": [(5, 4, 5)],
    },
]

_BRAND = {"email": "demo-brand@crecity.kr", "name": "데모브랜드"}


def _png(width: int, height: int, top: tuple, bottom: tuple) -> bytes:
    """세로 그라데이션 PNG를 표준 라이브러리만으로 생성한다(시드용 플레이스홀더 사진)."""
    rows = b""
    for y in range(height):
        t = y / (height - 1)
        r = round(top[0] + (bottom[0] - top[0]) * t)
        g = round(top[1] + (bottom[1] - top[1]) * t)
        b = round(top[2] + (bottom[2] - top[2]) * t)
        rows += b"\x00" + bytes((r, g, b)) * width

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows, 6))
        + chunk(b"IEND", b"")
    )


async def main() -> None:
    init_engine()
    storage = LocalPortfolioFileStorage()
    try:
        async with session_scope() as session:
            users = UserPgRepository(session)
            profiles = CreatorProfilePgRepository(session)
            packages = CreatorPackagePgRepository(session)
            portfolio = PortfolioItemPgRepository(session)

            brand = await users.find_by_email(_BRAND["email"]) or await users.create(
                email=_BRAND["email"], name=_BRAND["name"], account_type=AccountType.BRAND
            )

            order_seq = 0
            for demo in DEMO_CREATORS:
                if await profiles.exists_by_slug(demo["slug"]):
                    print(f"건너뜀(이미 있음): {demo['slug']}")
                    continue

                email = f"demo-{demo['slug']}@crecity.kr"
                user = await users.find_by_email(email) or await users.create(
                    email=email, name=demo["name"], account_type=AccountType.CREATOR
                )
                profile = await profiles.create(
                    slug=demo["slug"],
                    name=demo["name"],
                    tagline=demo["tagline"],
                    bio=demo["bio"],
                    location=demo["location"],
                    primary_category=demo["category"],
                    status=ProfileStatus.APPROVED,
                    user_id=user.id,
                )

                created_packages = [
                    await packages.create(
                        profile_id=profile.id,
                        platform=platform,
                        title=title,
                        description=description,
                        price_krw=price,
                    )
                    for platform, title, description, price in demo["packages"]
                ]

                top, bottom = demo["colors"]
                for i in range(3):
                    # 사진마다 톤을 조금씩 달리한다
                    shift = i * 14
                    content = _png(
                        800,
                        1000,
                        tuple(min(255, c + shift) for c in top),
                        tuple(max(0, c - shift) for c in bottom),
                    )
                    file_name = storage.save(content, "png")
                    await portfolio.create(profile_id=profile.id, file_name=file_name)

                # 완료 주문 + 리뷰 — 인기 순위·평점 표시용
                for scores in demo["reviews"][: demo["orders"]]:
                    order_seq += 1
                    package = created_packages[0]
                    order_row = await session.execute(
                        insert(OrderOrm)
                        .values(
                            package_id=package.id,
                            package_title=package.title,
                            brand_user_id=brand.id,
                            creator_user_id=user.id,
                            amount_krw=package.price_krw,
                            brand_fee_percent=5,
                            creator_fee_percent=15,
                            requirements=f"데모 주문 {order_seq} — 시연용 데이터입니다.",
                            status="COMPLETED",
                        )
                        .returning(OrderOrm.id)
                    )
                    order_id = order_row.scalar_one()
                    communication, timeliness, satisfaction = scores
                    await session.execute(
                        insert(ReviewOrm).values(
                            order_id=order_id,
                            brand_user_id=brand.id,
                            creator_user_id=user.id,
                            communication_score=communication,
                            timeliness_score=timeliness,
                            satisfaction_score=satisfaction,
                            comment="기획안부터 꼼꼼하게 챙겨주셔서 결과물이 기대 이상이었어요. 재구매 의사 있습니다.",
                        )
                    )
                await session.commit()
                print(f"생성: {demo['slug']} (패키지 {len(created_packages)} · 사진 3 · 주문 {demo['orders']})")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
