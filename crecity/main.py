import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from admin.adapter.inbound.api.v1.profile_review_router import profile_review_router
from admin.adapter.inbound.api.v1.steward_router import steward_router
from auth.adapter.inbound.api.v1.gatekeeper_router import gatekeeper_router
from auth.adapter.inbound.api.v1.logout_router import logout_router
from auth.adapter.inbound.api.v1.social_login_router import social_login_router
from auth.adapter.inbound.api.v1.token_refresh_router import token_refresh_router
from core.database import dispose_engine, init_engine
from core.database import ping as database_ping
from core.config import UPLOAD_DIR
from core.redis import dispose_redis, init_redis
from creator.adapter.inbound.api.v1.package_management_router import (
    package_management_router,
)
from creator.adapter.inbound.api.v1.my_profile_lookup_router import my_profile_lookup_router
from creator.adapter.inbound.api.v1.popular_profiles_router import popular_profiles_router
from creator.adapter.inbound.api.v1.profile_listing_router import profile_listing_router
from creator.adapter.inbound.api.v1.profile_lookup_router import profile_lookup_router
from creator.adapter.inbound.api.v1.profile_registration_router import (
    profile_registration_router,
)
from creator.adapter.inbound.api.v1.analytics_management_router import (
    analytics_management_router,
)
from creator.adapter.inbound.api.v1.faq_management_router import faq_management_router
from creator.adapter.inbound.api.v1.portfolio_management_router import (
    portfolio_management_router,
)
from creator.adapter.inbound.api.v1.profile_router import profile_router
from creator.adapter.inbound.api.v1.profile_update_router import profile_update_router
from auth.dependencies.access_token_verifier_provider import build_access_token_verifier
from creator.adapter.outbound.hub.package_summary_gateway import CreatorPackageSummaryGateway
from creator.adapter.outbound.hub.profile_review_gateway import CreatorProfileReviewGateway
from hub.adapter.inbound.api.v1.dispatcher_router import dispatcher_router
from hub.dependencies.current_user_provider import register_access_token_verifier
from hub.dependencies.custom_offer_provider import register_custom_offer_port
from hub.dependencies.package_summary_provider import register_package_summary_port
from hub.dependencies.profile_review_provider import register_profile_review_port
from order.adapter.inbound.api.v1.balance_lookup_router import balance_lookup_router
from order.adapter.inbound.api.v1.bookkeeper_router import bookkeeper_router
from order.adapter.inbound.api.v1.deliverable_submission_router import (
    deliverable_submission_router,
)
from order.adapter.inbound.api.v1.order_cancellation_router import order_cancellation_router
from order.adapter.inbound.api.v1.order_lookup_router import order_lookup_router
from order.adapter.inbound.api.v1.order_progress_router import order_progress_router
from order.adapter.outbound.hub.creator_popularity_gateway import OrderCreatorPopularityGateway
from order.adapter.outbound.hub.credit_balance_gateway import OrderCreditBalanceGateway
from order.adapter.outbound.hub.order_placement_gateway import PaidOrderPlacementGateway
from order.adapter.outbound.hub.withdrawal_settlement_gateway import OrderWithdrawalSettlementGateway
from order.adapter.inbound.api.v1.withdrawal_request_router import withdrawal_request_router
from admin.adapter.inbound.api.v1.withdrawal_settlement_router import withdrawal_settlement_router
from payment.adapter.inbound.api.v1.checkout_preparation_router import (
    checkout_preparation_router,
)
from payment.adapter.inbound.api.v1.payment_confirmation_router import (
    payment_confirmation_router,
)
from payment.adapter.inbound.api.v1.paymaster_router import paymaster_router
from hub.dependencies.campaign_application_provider import register_campaign_application_port
from hub.dependencies.credit_balance_provider import register_credit_balance_port
from hub.dependencies.order_placement_provider import register_order_placement_port
from creator.adapter.outbound.hub.creator_ref_gateway import CreatorRefGateway
from hub.dependencies.creator_ref_provider import register_creator_ref_port
from hub.dependencies.order_participants_provider import register_order_participants_port
from order.adapter.outbound.hub.order_participants_gateway import OrderParticipantsGateway
from auth.adapter.outbound.hub.user_directory_gateway import UserDirectoryGateway
from chat.adapter.inbound.api.v1.conversation_listing_router import (
    conversation_listing_router,
)
from chat.adapter.inbound.api.v1.conversation_opening_router import (
    conversation_opening_router,
)
from chat.adapter.inbound.api.v1.courier_router import courier_router
from chat.adapter.inbound.api.v1.offer_management_router import offer_management_router
from chat.adapter.outbound.hub.custom_offer_gateway import CustomOfferGateway
from chat.adapter.inbound.api.v1.messaging_router import messaging_router
from chat.adapter.inbound.api.v1.photo_messaging_router import photo_messaging_router
from hub.dependencies.user_directory_provider import register_user_directory_port
from campaign.adapter.inbound.api.v1.campaign_application_router import (
    campaign_application_router,
)
from campaign.adapter.inbound.api.v1.campaign_listing_router import campaign_listing_router
from campaign.adapter.inbound.api.v1.campaign_posting_router import campaign_posting_router
from campaign.adapter.outbound.hub.campaign_application_gateway import (
    CampaignApplicationGateway,
)
from campaign.adapter.inbound.api.v1.herald_router import herald_router
from notification.adapter.inbound.api.v1.bellman_router import bellman_router
from notification.adapter.inbound.api.v1.notification_listing_router import (
    notification_listing_router,
)
from hub.dependencies.creator_popularity_provider import register_creator_popularity_port
from hub.dependencies.withdrawal_settlement_provider import register_withdrawal_settlement_port
from hub.dependencies.creator_rating_provider import register_creator_rating_port
from review.adapter.outbound.hub.creator_rating_gateway import ReviewCreatorRatingGateway
from review.adapter.inbound.api.v1.appraiser_router import appraiser_router
from review.adapter.inbound.api.v1.review_listing_router import review_listing_router
from review.adapter.inbound.api.v1.review_submission_router import review_submission_router

# 스타 토폴로지 조립 지점 — 스포크 구현체를 허브 계약에 등록한다
# (스포크끼리는 허브 포트로만 협력한다).
register_access_token_verifier(build_access_token_verifier())  # auth → 현재 사용자
register_package_summary_port(CreatorPackageSummaryGateway())
register_custom_offer_port(CustomOfferGateway())  # creator → 패키지 요약
register_profile_review_port(CreatorProfileReviewGateway())  # creator → 프로필 심사
register_order_placement_port(PaidOrderPlacementGateway())  # order → 결제 완료 주문 생성
register_order_participants_port(OrderParticipantsGateway())  # order → 주문 당사자(리뷰 자격)
register_creator_ref_port(CreatorRefGateway())  # creator → 크리에이터 참조(리뷰·캠페인·채팅)
register_user_directory_port(UserDirectoryGateway())  # auth → 회원 디렉토리(채팅 상대 표시)
register_creator_rating_port(ReviewCreatorRatingGateway())  # review → 평점 요약(목록 카드)
register_creator_popularity_port(OrderCreatorPopularityGateway())  # order → 인기 순위(홈 섹션)
register_withdrawal_settlement_port(OrderWithdrawalSettlementGateway())  # order → 인출 운영 처리
register_credit_balance_port(OrderCreditBalanceGateway())  # order → 크레딧 잔액(체크아웃 적용액 확정)
register_campaign_application_port(CampaignApplicationGateway())  # campaign → 지원 수락 결제


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    init_redis()
    yield
    await dispose_redis()
    await dispose_engine()


app = FastAPI(title="crecity API", lifespan=lifespan)

# 업로드 파일 정적 서빙 — 프론트는 /api/backend/uploads/... 로 접근한다.
os.makedirs(os.path.join(UPLOAD_DIR, "portfolio"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(dispatcher_router)
app.include_router(gatekeeper_router)
app.include_router(social_login_router)
app.include_router(token_refresh_router)
app.include_router(logout_router)
app.include_router(profile_router)
app.include_router(profile_registration_router)
app.include_router(profile_listing_router)
app.include_router(popular_profiles_router)
app.include_router(my_profile_lookup_router)
app.include_router(profile_update_router)
app.include_router(portfolio_management_router)
app.include_router(analytics_management_router)
app.include_router(faq_management_router)
app.include_router(profile_lookup_router)
app.include_router(package_management_router)
app.include_router(bookkeeper_router)
app.include_router(order_progress_router)
app.include_router(order_cancellation_router)
app.include_router(deliverable_submission_router)
app.include_router(order_lookup_router)
app.include_router(balance_lookup_router)
app.include_router(withdrawal_request_router)
app.include_router(withdrawal_settlement_router)
app.include_router(steward_router)
app.include_router(profile_review_router)
app.include_router(paymaster_router)
app.include_router(checkout_preparation_router)
app.include_router(payment_confirmation_router)
app.include_router(appraiser_router)
app.include_router(review_submission_router)
app.include_router(review_listing_router)
app.include_router(herald_router)
app.include_router(campaign_posting_router)
app.include_router(campaign_listing_router)
app.include_router(campaign_application_router)
app.include_router(courier_router)
app.include_router(conversation_opening_router)
app.include_router(conversation_listing_router)
app.include_router(messaging_router)
app.include_router(photo_messaging_router)
app.include_router(offer_management_router)
app.include_router(bellman_router)
app.include_router(notification_listing_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "database": await database_ping()}
