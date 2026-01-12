from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_helper import db_helper
from core.logging import logging
from core.schemas.pagination import Pagination
from core.utils.dependencies import require_permission
from models.user import User

from .services import ResultService

# Logger obyektini sozlash
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Result"], 
    prefix="/results"
)


def get_result_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> ResultService:
    return ResultService(session=session)


@router.get(
    "/{result_id}",
    summary="Natijani ID bo'yicha olish",
    description="Muayyan test topshirish natijasi haqidagi to'liq ma'lumotni ko'rish."
)
async def get_by_id_result(
    result_id: int,
    service: ResultService = Depends(get_result_service),
    current_user: User = Depends(require_permission("results:retrieve")),
):
    logger.info(f"GET /results/{result_id} - Foydalanuvchi {current_user.id} natijani ko'rmoqda")
    return await service.get_by_id_result(result_id=result_id)


@router.get(
    "",
    summary="Test bo'yicha barcha natijalarni olish",
    description="Muayyan test (quiz_id) bo'yicha barcha topshirilgan natijalar ro'yxatini ko'rish."
)
async def get_all_result_by_quiz(
    quiz_id: int,
    pagination: Pagination = Depends(),
    service: ResultService = Depends(get_result_service),
    current_user: User = Depends(require_permission("results:all")),
):
    logger.info(
        f"GET /results - Foydalanuvchi {current_user.id} quiz_id {quiz_id} bo'yicha natijalarni olmoqda (Sahifa: {pagination.page})"
    )
    return await service.get_all_result_by_quiz(
        quiz_id=quiz_id, 
        pagination=pagination
    )