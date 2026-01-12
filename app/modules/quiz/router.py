from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_helper import db_helper
from core.schemas.pagination import Pagination
from core.utils.dependencies import require_permission
from models.user import User
from core.logging import logging  

from .schemas import (
    EndQuizCreate,
    QuizCreateRequest,
    QuizListResponse,
    QuizResponse,
    QuizUpdate,
    QuizResultResponse,
)
from .services import QuizService

# Logger obyektini yaratamiz
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/quizzes",
    tags=["Quiz"],
)

def get_quiz_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> QuizService:
    return QuizService(session=session)

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=QuizResponse,
    summary="Yangi test yaratish",
    description="O'qituvchi tomonidan yangi test yaratish. `user_id` orqali test biriktirilgan o'qituvchi ko'rsatiladi."
)
async def create_quiz(
    user_id: int = Query(..., description="Testga mas'ul o'qituvchi ID-si"),
    data: QuizCreateRequest = None,
    current_user: User = Depends(require_permission("quizzes:create")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    logger.info(f"POST /quizzes - User {current_user.id} yangi test yaratmoqda (O'qituvchi ID: {user_id})")
    return await service.create_quiz(
        data=data,
        user_id=user_id,
    )

@router.post(
    "/start",
    response_model=dict,
    summary="Testni boshlash va foydalanuvchini autentifikatsiya qilish",
    description="Foydalanuvchi PIN-kod va rasm orqali testni boshlaydi. Tizim foydalanuvchi shaxsini tekshiradi."
)
async def start_quiz(
    quiz_id: int,
    pin: str,
    user_image: UploadFile = File(..., description="Foydalanuvchini identifikatsiya qilish uchun rasm (selfie)"),
    current_user: User = Depends(require_permission("quizzes:start")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResultResponse:
    logger.info(f"POST /quizzes/start - User {current_user.id} testni boshlamoqda (Quiz ID: {quiz_id})")
    return await service.start_quiz(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        quiz_id=quiz_id,
        user_image=user_image,
        pin=pin,
    )

@router.post(
    "/end",
    summary="Testni yakunlash va natijalarni saqlash",
    description="Foydalanuvchi tomonidan topshirilgan testni yakunlash va to'plangan ballarni hisoblash."
)
async def end_quiz(
    current_user: User = Depends(require_permission("quizzes:end")),
    data: EndQuizCreate = None,
    service: QuizService = Depends(get_quiz_service),
):
    logger.info(f"POST /quizzes/end - User {current_user.id} testni yakunlamoqda (Quiz ID: {data.quiz_id if data else 'unknown'})")
    return await service.end_quiz(
        data=data,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
    )

@router.get(
    "",
    response_model=QuizListResponse,
    summary="Barcha testlar ro'yxatini olish",
    description="Tizimdagi barcha mavjud testlarni sahifalangan (pagination) ko'rinishda olish."
)
async def get_all_quiz(
    pagination: Pagination = Depends(),
    current_user: User = Depends(require_permission("quizzes:all")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizListResponse:
    logger.info(f"GET /quizzes - User {current_user.id} testlar ro'yxatini olmoqda (Sahifa: {pagination.page})")
    return await service.get_all_quiz(
        pagination=pagination,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
    )

@router.get(
    "/{quiz_id}",
    response_model=QuizResponse,
    summary="Testni ID bo'yicha olish",
    description="Muayyan bir testning to'liq ma'lumotlarini ID orqali ko'rish."
)
async def get_quiz_by_id(
    quiz_id: int,
    current_user: User = Depends(require_permission("quizzes:retrieve")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    logger.info(f"GET /quizzes/{quiz_id} - User {current_user.id} test ma'lumotlarini ko'rmoqda")
    return await service.get_quiz_by_id(
        quiz_id=quiz_id,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
    )

@router.put(
    "/{quiz_id}",
    response_model=QuizResponse,
    summary="Test ma'lumotlarini tahrirlash",
    description="Mavjud testning parametrlarini o'zgartirish."
)
async def update_quiz(
    quiz_id: int,
    current_user: User = Depends(require_permission("quizzes:update")),
    data: QuizUpdate = None,
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    logger.info(f"PUT /quizzes/{quiz_id} - User {current_user.id} testni tahrirlamoqda")
    return await service.update_quiz(
        quiz_id=quiz_id,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        data=data,
    )

@router.delete(
    "/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Testni tizimdan o'chirish",
    description="ID bo'yicha testni butunlay o'chirib tashlash."
)
async def delete_quiz(
    quiz_id: int,
    current_user: User = Depends(require_permission("quizzes:delete")),
    service: QuizService = Depends(get_quiz_service),
) -> None:
    logger.info(f"DELETE /quizzes/{quiz_id} - User {current_user.id} testni o'chirmoqda")
    await service.delete_quiz(
        quiz_id=quiz_id,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
    )