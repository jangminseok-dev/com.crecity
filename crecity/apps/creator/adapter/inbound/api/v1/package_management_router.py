from fastapi import APIRouter, Depends, HTTPException

from creator.adapter.inbound.api.schemas.package_management_schema import (
    PackageResponseSchema,
    PackageWriteRequestSchema,
)
from creator.app.dtos.package_management_dto import (
    PackageListQuery,
    PackageRegistrationCommand,
    PackageRemovalCommand,
    PackageUpdateCommand,
)
from creator.app.exceptions import (
    NotProfileOwnerError,
    PackageNotFoundError,
    ProfileNotFoundError,
)
from creator.app.ports.input.package_management_use_case import PackageManagementUseCase
from creator.dependencies.package_management_provider import get_package_management_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

package_management_router = APIRouter(prefix="/creator", tags=["creator"])


def _to_schema(result) -> PackageResponseSchema:
    return PackageResponseSchema(
        id=result.id,
        profile_id=result.profile_id,
        platform=result.platform,
        title=result.title,
        description=result.description,
        price_krw=result.price_krw,
        revision_limit=result.revision_limit,
        usage_rights=result.usage_rights,
        created_at=result.created_at,
    )


@package_management_router.post(
    "/profiles/{slug}/packages", response_model=PackageResponseSchema, status_code=201
)
async def register_package(
    slug: str,
    body: PackageWriteRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: PackageManagementUseCase = Depends(get_package_management_use_case),
) -> PackageResponseSchema:
    try:
        result = await use_case.register(
            PackageRegistrationCommand(
                slug=slug,
                platform=body.platform,
                title=body.title,
                description=body.description,
                price_krw=body.price_krw,
                revision_limit=body.revision_limit,
                usage_rights=body.usage_rights,
                requester_user_id=user.id,
            )
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotProfileOwnerError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@package_management_router.get(
    "/profiles/{slug}/packages", response_model=list[PackageResponseSchema]
)
async def list_packages(
    slug: str,
    use_case: PackageManagementUseCase = Depends(get_package_management_use_case),
) -> list[PackageResponseSchema]:
    try:
        results = await use_case.list_for_profile(PackageListQuery(slug=slug))
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return [_to_schema(result) for result in results]


@package_management_router.put(
    "/packages/{package_id}", response_model=PackageResponseSchema
)
async def update_package(
    package_id: int,
    body: PackageWriteRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: PackageManagementUseCase = Depends(get_package_management_use_case),
) -> PackageResponseSchema:
    try:
        result = await use_case.update(
            PackageUpdateCommand(
                package_id=package_id,
                platform=body.platform,
                title=body.title,
                description=body.description,
                price_krw=body.price_krw,
                revision_limit=body.revision_limit,
                usage_rights=body.usage_rights,
                requester_user_id=user.id,
            )
        )
    except PackageNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotProfileOwnerError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@package_management_router.delete("/packages/{package_id}", status_code=204)
async def remove_package(
    package_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: PackageManagementUseCase = Depends(get_package_management_use_case),
) -> None:
    try:
        await use_case.remove(
            PackageRemovalCommand(package_id=package_id, requester_user_id=user.id)
        )
    except PackageNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotProfileOwnerError as error:
        raise HTTPException(status_code=403, detail=str(error))
