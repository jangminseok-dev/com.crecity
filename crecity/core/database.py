from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import DATABASE_URL

logger = logging.getLogger("uvicorn.error")


class Base(DeclarativeBase):
    pass


engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    global engine, _session_factory
    if engine is not None:
        return
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
    _session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def dispose_engine() -> None:
    global engine, _session_factory
    if engine is not None:
        await engine.dispose()
        engine = None
        _session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        init_engine()
    if _session_factory is None:
        raise RuntimeError("DB 엔진이 초기화되지 않았습니다.")
    async with _session_factory() as session:
        yield session


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI DI 밖(허브 게이트웨이·스크립트)에서 쓰는 세션 컨텍스트."""
    if _session_factory is None:
        init_engine()
    if _session_factory is None:
        raise RuntimeError("DB 엔진이 초기화되지 않았습니다.")
    async with _session_factory() as session:
        yield session


async def ping() -> bool:
    """공유 DB에 `SELECT 1`을 던져 살아 있는지 본다 (/health 전용).

    엔진은 기동 시 lazy 초기화라 모듈 상수로 잡아두면 None에 묶인다 — 호출 시점에 읽는다.
    """
    if engine is None:
        return False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # 원인은 /health 응답에 싣지 않는다 — 공개 엔드포인트
        logger.exception("DB 헬스체크 실패")
        return False
