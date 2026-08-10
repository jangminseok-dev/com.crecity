import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps"))

from fastapi import FastAPI

from auth.adapter.inbound.api.v1.gatekeeper_router import gatekeeper_router
from core.database import dispose_engine, init_engine
from core.database import ping as database_ping
from creator.adapter.inbound.api.v1.package_management_router import (
    package_management_router,
)
from creator.adapter.inbound.api.v1.profile_listing_router import profile_listing_router
from creator.adapter.inbound.api.v1.profile_lookup_router import profile_lookup_router
from creator.adapter.inbound.api.v1.profile_registration_router import (
    profile_registration_router,
)
from creator.adapter.inbound.api.v1.profile_router import profile_router
from hub.adapter.inbound.api.v1.dispatcher_router import dispatcher_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    yield
    await dispose_engine()


app = FastAPI(title="crecity API", lifespan=lifespan)

app.include_router(dispatcher_router)
app.include_router(gatekeeper_router)
app.include_router(profile_router)
app.include_router(profile_registration_router)
app.include_router(profile_listing_router)
app.include_router(profile_lookup_router)
app.include_router(package_management_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "database": await database_ping()}
