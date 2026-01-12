from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from .services import PermissionService
from .schemas import CreatePermissionRequest
from core.logging import logging
from core.schemas.pagination import Pagination
from core.db_helper import db_helper
from core.utils.dependencies import require_permission
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Permission"],
    prefix="/permission",
)

async def get_permission_service(session: AsyncSession = Depends(db_helper.session_getter)) -> PermissionService:
    return PermissionService(session=session)

@router.post("", status_code=status.HTTP_201_CREATED, summary="Yangi ruxsat yaratish")
async def create_permission(
    data: CreatePermissionRequest,
    current_user: User = Depends(require_permission("permission:create")),
    service: PermissionService = Depends(get_permission_service),
):
    logger.info(f"POST /permission - Foydalanuvchi {current_user.id} yangi ruxsat yaratmoqda: {data.name}")
    return await service.create_permission(data)

@router.get("/{permission_id}", summary="Ruxsatni ID bo'yicha olish")
async def get_permission_by_id(
    permission_id: int,
    current_user: User = Depends(require_permission("permission:retrieve")),
    service: PermissionService = Depends(get_permission_service),
):
    logger.info(f"GET /permission/{permission_id} - Foydalanuvchi {current_user.id} ruxsatni olmoqda")
    return await service.get_permission_by_id(permission_id)

@router.get("", summary="Barcha ruxsatlar ro'yxati")
async def get_all_permissions(
    pagination: Pagination = Depends(),
    current_user: User = Depends(require_permission("permission:all")),
    service: PermissionService = Depends(get_permission_service),
):
    logger.info(f"GET /permission - Foydalanuvchi {current_user.id} ruxsatlarni ko'rmoqda")
    return await service.get_all_permissions(pagination)

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Ruxsatni o'chirish")
async def delete_permission(
    permission_id: int,
    current_user: User = Depends(require_permission("permission:delete")),
    service: PermissionService = Depends(get_permission_service),
):
    logger.info(f"DELETE /permission/{permission_id} - Foydalanuvchi {current_user.id} ruxsatni o'chirmoqda")
    await service.delete_permission(permission_id)

@router.get("/resource/{resource}", summary="Resurs bo'yicha ruxsatlarni olish")
async def get_permission_by_resource(
    resource: str,
    current_user: User = Depends(require_permission("permission:resource")),
    service: PermissionService = Depends(get_permission_service),
):
    logger.info(f"GET /permission/resource/{resource} - Foydalanuvchi {current_user.id} '{resource}' bo'yicha ruxsatlarni olmoqda")
    return await service.get_permission_by_resource(resource)