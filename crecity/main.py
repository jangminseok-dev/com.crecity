import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps"))

from fastapi import FastAPI

from auth.adapter.inbound.api.v1.gatekeeper_router import gatekeeper_router
from auth.adapter.inbound.api.v1.social_login_router import social_login_router
from auth.adapter.inbound.api.v1.token_refresh_router import token_refresh_router
from core.database import dispose_engine, init_engine
from core.database import ping as database_ping
from core.redis import dispose_redis, init_redis
from creator.adapter.inbound.api.v1.package_management_router import (
    package_management_router,
)
from creator.adapter.inbound.api.v1.my_profile_lookup_router import my_profile_lookup_router
from creator.adapter.inbound.api.v1.profile_listing_router import profile_listing_router
from creator.adapter.inbound.api.v1.profile_lookup_router import profile_lookup_router
from creator.adapter.inbound.api.v1.profile_registration_router import (
    profile_registration_router,
)
from creator.adapter.inbound.api.v1.profile_router import profile_router
from auth.dependencies.access_token_verifier_provider import build_access_token_verifier
from creator.adapter.outbound.hub.package_summary_gateway import CreatorPackageSummaryGateway
from hub.adapter.inbound.api.v1.dispatcher_router import dispatcher_router
from hub.dependencies.current_user_provider import register_access_token_verifier
from hub.dependencies.package_summary_provider import register_package_summary_port
from order.adapter.inbound.api.v1.balance_lookup_router import balance_lookup_router
from order.adapter.inbound.api.v1.bookkeeper_router import bookkeeper_router
from order.adapter.inbound.api.v1.order_lookup_router import order_lookup_router
from order.adapter.inbound.api.v1.order_placement_router import order_placement_router
from order.adapter.inbound.api.v1.order_progress_router import order_progress_router

# 스타 토폴로지 조립 지점 — 스포크 구현체를 허브 계약에 등록한다
# (스포크끼리는 허브 포트로만 협력한다).
register_access_token_verifier(build_access_token_verifier())  # auth → 현재 사용자
register_package_summary_port(CreatorPackageSummaryGateway())  # creator → 패키지 요약


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    init_redis()
    yield
    await dispose_redis()
    await dispose_engine()


app = FastAPI(title="crecity API", lifespan=lifespan)

app.include_router(dispatcher_router)
app.include_router(gatekeeper_router)
app.include_router(social_login_router)
app.include_router(token_refresh_router)
app.include_router(profile_router)
app.include_router(profile_registration_router)
app.include_router(profile_listing_router)
app.include_router(my_profile_lookup_router)
app.include_router(profile_lookup_router)
app.include_router(package_management_router)
app.include_router(bookkeeper_router)
app.include_router(order_placement_router)
app.include_router(order_progress_router)
app.include_router(order_lookup_router)
app.include_router(balance_lookup_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "database": await database_ping()}
