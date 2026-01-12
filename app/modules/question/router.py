from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from .services import QuestionsService
from .schemas import QuestionUpdateRequest, QuestionRequest

from core.schemas.pagination import Pagination
from core.db_helper import db_helper
from core.logging import logging
from core.utils.dependencies import require_permission
from models.user import User
from core.utils.save_file import save_file


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/questions",
    tags=["Questions"],
)


def get_question_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> QuestionsService:
    return QuestionsService(session=session)


@router.post(
    "", 
    summary="Bitta savol yaratish",
    description="Tizimga yangi savol qo'shish. Savol matni va 4 ta javob varianti yuborilishi shart."
)
async def create_question(
    quiz_id: int,
    data: QuestionRequest,
    current_user: User = Depends(require_permission("questions:create")),
    service: QuestionsService = Depends(get_question_service),
):
    logger.info(f"POST /questions - User {current_user.id} creating a question")
    return await service.create_question(
        user_id=current_user.id, 
        quiz_id=quiz_id, 
        data=data
    )

@router.post(
    "/upload", 
    summary="Fayl yuklash",
    description="Savolga rasm yoki boshqa fayllarni biriktirish uchun serverga yuklash."
)
async def upload_file(
    upload_file: UploadFile = File(),
    _: User = Depends(require_permission("questions:upload")),
):
    url = save_file(file=upload_file, subdir="question")
    return {"file_url": url}

@router.post(
    "/bulk-upload",
    summary="Excel orqali ommaviy yuklash",
    description="Excel (.xlsx) fayli yordamida ko'plab savollarni bir vaqtda yaratish. Faylda text, option_a, option_b, option_c, option_d ustunlari bo'lishi shart."
)
async def create_questions_bulk(
    quiz_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("questions:batch")),
    service: QuestionsService = Depends(get_question_service),
):
    logger.info(f"POST /questions/bulk-upload - User {current_user.id} uploading Excel file")
    file_content = await file.read()
    return await service.create_questions_bulk_excel(
        user_id=current_user.id,
        quiz_id=quiz_id,
        file_content=file_content,
    )

@router.get(
    "/{question_id}", 
    summary="Savolni ID bo'yicha olish",
    description="Muayyan savol ma'lumotlarini uning ID-si orqali olish. Adminlar hamma savollarni, o'qituvchilar esa faqat o'z savollarini ko'ra oladilar."
)
async def get_question_by_id(
    question_id: int,
    current_user: User = Depends(require_permission("questions:retrieve")),
    service: QuestionsService = Depends(get_question_service),
):
    return await service.get_question_by_id(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        question_id=question_id,
    )

@router.get(
    "", 
    summary="Barcha savollar ro'yxati",
    description="Tizimdagi savollarni sahifalangan ko'rinishda olish."
)
async def get_all_questions(
    pagination: Pagination = Depends(),
    current_user: User = Depends(require_permission("questions:all")),
    service: QuestionsService = Depends(get_question_service),
):
    return await service.get_all_questions(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        pagination=pagination,
    )

@router.put(
    "/{question_id}", 
    summary="Savolni tahrirlash",
    description="Mavjud savolning matni yoki variantlarini yangilash."
)
async def update_question(
    question_id: int,
    data: QuestionUpdateRequest,
    current_user: User = Depends(require_permission("questions:update")),
    service: QuestionsService = Depends(get_question_service),
):
    return await service.update_question(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        question_id=question_id,
        data=data,
    )

@router.delete(
    "/{question_id}", 
    summary="Savolni o'chirish",
    description="Savolni ma'lumotlar bazasidan butunlay o'chirib tashlash."
)
async def delete_question(
    question_id: int,
    current_user: User = Depends(require_permission("questions:delete")),
    service: QuestionsService = Depends(get_question_service),
):
    return await service.delete_question(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        question_id=question_id,
    )