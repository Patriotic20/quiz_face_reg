from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status, UploadFile

from core.logging import logging
from core.mixins.crud import create
from core.config import settings
from core.schemas.pagination import Pagination

from models.results import Result
from models.quiz import Quiz
from models.user import User

from .schemas import (
    QuizUpdate,
    QuizCreateRequest,
    QuizCreate,
    QuizResponse,
    QuizListResponse,
    EndQuizCreate,
    QuizResultResponse,

)
from .utils.compare_faces import compare_faces



logger = logging.getLogger(__name__)


class QuizService:
    """Service for managing quiz operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_quiz(
        self, data: QuizCreateRequest, user_id: int
    ) -> QuizResponse:
        """Create a new quiz for a subject"""
        logger.info(
            f"Attempting to create quiz for user: {user_id}"
        )
        
        user_data = await self.session.get(User, user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID-si {user_id} bo'lgan foydalanuvchi topilmadi"
            )
        try:
            quiz_data = QuizCreate(
                user_id=user_id,
                **data.model_dump(),
            )
            new_quiz = await create(
                session=self.session, model=Quiz, data=quiz_data
            )
            logger.info(
                f"Quiz created successfully: {new_quiz.id} by user {user_id}"
            )
            return QuizResponse.model_validate(new_quiz)
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"Quiz creation failed for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                # Ma'lumotlar bazasidagi cheklovlar buzilganda (masalan, takroriy nom yoki noto'g'ri fan ID-si)
                detail="Test ma'lumotlari noto'g'ri - fan mavjud emas yoki ma'lumotlarda ziddiyat bor"
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during quiz creation for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Test yaratishda kutilmagan xatolik yuz berdi"
            )

    async def get_quiz_by_id(
        self, user_id: int, user_role: str, quiz_id: int
    ) -> QuizResponse:
        """Get a quiz by ID with authorization check"""
        logger.info(
            f"Fetching quiz {quiz_id} for user {user_id} with role {user_role}"
        )
        try:
            stmt = select(Quiz).where(Quiz.id == quiz_id)

            # Faqat admin bo'lmasa, user_id bo'yicha filtr qo'llaniladi
            if user_role != settings.admin.name:
                stmt = stmt.where(Quiz.user_id == user_id)

            result = await self.session.execute(stmt)
            quiz_data = result.scalars().first()

            if not quiz_data:
                logger.warning(
                    f"Quiz {quiz_id} not found for user {user_id} with role {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    # Test topilmaganda yoki foydalanuvchida unga ruxsat bo'lmaganda
                    detail=f"ID-si {quiz_id} bo'lgan test topilmadi yoki sizda uni ko'rish uchun ruxsat yo'q"
                )

            logger.info(f"Quiz {quiz_id} retrieved successfully")
            return QuizResponse.model_validate(quiz_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while fetching quiz {quiz_id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                # Bazadan ma'lumot olishda texnik xatolik yuz bersa
                detail="Test ma'lumotlarini olishda kutilmagan xatolik yuz berdi"
            )

    async def get_all_quiz(
        self, user_id: int, user_role: str, pagination: Pagination
    ) -> QuizListResponse:
        """Get all quizzes with pagination and authorization"""
        logger.info(
            f"Fetching quizzes for user {user_id} with role {user_role} "
            f"- page: {pagination.page}, limit: {pagination.limit}"
        )
        try:
            # Build count query
            count_stmt = select(func.count(Quiz.id))
            if user_role != settings.admin.name:
                count_stmt = count_stmt.where(Quiz.user_id == user_id)

            # Get total count
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Build data query
            stmt = select(Quiz)
            if user_role != settings.admin.name:
                stmt = stmt.where(Quiz.user_id == user_id)

            stmt = (
                stmt.order_by(Quiz.created_at.desc())
                .limit(pagination.limit)
                .offset(pagination.offset)
            )

            # Get paginated results
            result = await self.session.execute(stmt)
            quiz_data = result.scalars().all()

            # Calculate total pages
            total_pages = (total + pagination.limit - 1) // pagination.limit

            logger.info(
                f"Retrieved {len(quiz_data)} quizzes out of {total} total for user {user_id}"
            )

            return QuizListResponse(
                total=total,
                page=pagination.page,
                limit=pagination.limit,
                total_pages=total_pages,
                quizzes=[
                    QuizResponse.model_validate(quiz) for quiz in quiz_data
                ],
            )

        except Exception as e:
            logger.error(
                f"Unexpected error while fetching quizzes for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                # Testlar ro'yxatini yuklashda tizimda xatolik yuz berganda
                detail="Testlar ro'yxatini olishda kutilmagan xatolik yuz berdi"
            )

    async def update_quiz(
        self, quiz_id: int, user_id: int, user_role: str, data: QuizUpdate
    ) -> QuizResponse:
        """Update a quiz with authorization check"""
        logger.info(
            f"Attempting to update quiz {quiz_id} for user {user_id} with role {user_role}"
        )
        try:
            # Build query to find the quiz
            stmt = select(Quiz).where(Quiz.id == quiz_id)

            # Only apply user_id filter if not admin
            if user_role != settings.admin.name:
                stmt = stmt.where(Quiz.user_id == user_id)

            # Get the quiz
            result = await self.session.execute(stmt)
            quiz_data = result.scalars().first()

            # Check if quiz exists
            if not quiz_data:
                logger.warning(
                    f"Quiz {quiz_id} not found for user {user_id} with role {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    # Test topilmaganda yoki tahrirlashga ruxsat bo'lmaganda
                    detail=f"ID-si {quiz_id} bo'lgan test topilmadi yoki uni tahrirlash uchun ruxsatingiz yo'q"
                )

            # Update quiz fields
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(quiz_data, field, value)

            # Commit changes
            self.session.add(quiz_data)
            await self.session.flush()
            await self.session.commit()

            # Refresh to reload lazy-loaded attributes
            await self.session.refresh(quiz_data)

            logger.info(f"Quiz {quiz_id} updated successfully by user {user_id}")
            return QuizResponse.model_validate(quiz_data)

        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(
                f"Quiz update failed for quiz {quiz_id}, user {user_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                # Ma'lumotlar bazasida ziddiyat yuzaga kelsa (masalan, takroriy PIN yoki nom)
                detail="Test ma'lumotlari noto'g'ri - ma'lumotlarda ziddiyat bor yoki fan mavjud emas"
            )
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while updating quiz {quiz_id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                # Yangilash jarayonida texnik xatolik yuz bersa
                detail="Testni yangilashda kutilmagan xatolik yuz berdi"
            )

    async def delete_quiz(
            self, quiz_id: int, user_id: int, user_role: str
        ) -> dict:
            """Delete a quiz with authorization check"""
            logger.info(
                f"Attempting to delete quiz {quiz_id} for user {user_id} with role {user_role}"
            )
            try:
                # Testni topish uchun so'rov yaratish
                stmt = select(Quiz).where(Quiz.id == quiz_id)

                # Agar admin bo'lmasa, faqat o'ziga tegishli testni o'chira oladi
                if user_role != settings.admin.name:
                    stmt = stmt.where(Quiz.user_id == user_id)

                result = await self.session.execute(stmt)
                quiz_data = result.scalars().first()

                # Test mavjudligini tekshirish
                if not quiz_data:
                    logger.warning(
                        f"Quiz {quiz_id} not found for user {user_id} with role {user_role}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        # Test topilmaganda yoki o'chirishga huquq bo'lmaganda
                        detail=f"ID-si {quiz_id} bo'lgan test topilmadi yoki uni o'chirish uchun ruxsatingiz yo'q"
                    )

                # Testni o'chirish
                await self.session.delete(quiz_data)
                await self.session.commit()

                logger.info(f"Quiz {quiz_id} deleted successfully by user {user_id}")
                return {
                    "message": f"Test {quiz_id} muvaffaqiyatli o'chirildi",
                    "quiz_id": quiz_id,
                }

            except HTTPException:
                raise
            except Exception as e:
                await self.session.rollback()
                logger.error(
                    f"Unexpected error while deleting quiz {quiz_id} for user {user_id}: {str(e)}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    # O'chirish jarayonida texnik xatolik yuz bersa
                    detail="Testni o'chirishda kutilmagan xatolik yuz berdi"
                )
            
    async def start_quiz(
            self, 
            user_id: int,
            user_image: UploadFile,
            user_role: str, 
            quiz_id: int, 
            pin: str
        ):
            """
            Foydalanuvchi uchun testni barcha tekshiruvlardan o'tkazgan holda boshlash.
            Args:
                user_id: Foydalanuvchi ID-si
                user_image: Yuzni tekshirish (Face ID) uchun yuklangan rasm
                user_role: Foydalanuvchi roli (admin, student, guest)
                quiz_id: Boshlanadigan test ID-si
                pin: Test uchun kirish PIN-kodi
            Returns:
                dict: Savollar bilan birga test ma'lumotlari
            Raises:
                HTTPException: Agar test topilmasa, PIN noto'g'ri bo'lsa yoki yuz mos kelmasa
            """
            # Foydalanuvchi rolini tekshirish
            valid_roles = {"admin", "student", "guest"}
            if user_role.lower() not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Foydalanuvchi roli noto'g'ri: {user_role}"
                )
            
            # Foydalanuvchi yuzini bazadagi rasm bilan solishtirish
            # (Bu metod ichidagi xatoliklar ham o'zbek tilida bo'lishi kerak)
            await self.get_user_and_check(user_id=user_id, img2_file=user_image)
            
            # Testni savollari bilan birga olish (bitta so'rovda)
            quiz_stmt = select(Quiz).where(Quiz.id == quiz_id).options(
                selectinload(Quiz.questions)
            )
            quiz_result = await self.session.execute(quiz_stmt)
            quiz_data = quiz_result.scalars().first()
            
            # Test mavjudligini tekshirish
            if not quiz_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ID-si {quiz_id} bo'lgan test topilmadi"
                )
            
            # PIN-kodni tekshirish
            if quiz_data.pin != pin:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Ushbu test uchun kiritilgan PIN-kod noto'g'ri"
                )
            
            # Ma'lumotlarni qaytarish
            return {
                "quiz_id": quiz_data.id,
                "quiz_name": quiz_data.name,
                "quiz_number": quiz_data.quiz_number,
                "duration": quiz_data.during,
                "total_questions": len(quiz_data.questions),
                "questions": [
                    q.to_dict(randomize_options=True)
                    for q in quiz_data.questions
                ],
            }
            
    async def end_quiz(self, user_id: int, user_role: str, data: EndQuizCreate) -> QuizResultResponse:
            """
            Testni yakunlash va natijalarni hisoblash.
            
            Args:
                user_id: Foydalanuvchi ID-si
                user_role: Foydalanuvchi roli (admin, student, guest)
                data: Topshirilgan javoblar ma'lumotlari
                
            Returns:
                QuizResultResponse: Ballar va baho bilan test natijalari
                
            Raises:
                HTTPException/ValueError: Agar foydalanuvchi roli noto'g'ri bo'lsa yoki test topilmasa
            """
            # Foydalanuvchi rolini tekshirish
            valid_roles = {"admin", "student", "guest"}
            if user_role.lower() not in valid_roles:
                # Agar bu yerda HTTPException ishlatsangiz yaxshiroq:
                raise ValueError(f"Foydalanuvchi roli noto'g'ri: {user_role}")
            
            # Test va savollarni olish
            quiz_stmt = select(Quiz).where(Quiz.id == data.quiz_id).options(
                selectinload(Quiz.questions)
            )
            quiz_result = await self.session.execute(quiz_stmt)
            quiz_data = quiz_result.scalars().first()
            
            if not quiz_data:
                raise ValueError(f"ID-si {data.quiz_id} bo'lgan test topilmadi")
            
            # To'g'ri javoblarni hisoblash
            correct_count = 0
            question_map = {q.id: q for q in quiz_data.questions}
            
            for answer in data.answers:
                question = question_map.get(answer.question_id)
                # Savol mavjudligini va javob variantini tekshirish (option_a - to'g'ri javob deb hisoblanganda)
                if question and question.option_a == answer.option:
                    correct_count += 1
            
            # Ball va bahoni hisoblash
            total_questions = len(quiz_data.questions)
            incorrect_count = total_questions - correct_count
            score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
            grade = self._calculate_grade(score_percentage)
            
            # Natijani ma'lumotlar bazasiga saqlash
            result = Result(
                user_id=user_id,
                quiz_id=data.quiz_id,
                correct_answers=correct_count,
                incorrect_answers=incorrect_count,
                total_questions=total_questions,
                score_percentage=score_percentage,
                grade=grade
            )
            self.session.add(result)
            await self.session.commit()
            
            # Natijani qaytarish
            return QuizResultResponse(
                quiz_id=data.quiz_id,
                total_questions=total_questions,
                correct_answers=correct_count,
                incorrect_answers=incorrect_count,
                score_percentage=round(score_percentage, 2),
                grade=grade
            )
    
    @staticmethod
    def _calculate_grade(score_percentage: float) -> str:
        """Calculate letter grade based on score percentage."""
        if score_percentage >= 90:
            return "A+"
        elif score_percentage >= 80:
            return "A"
        elif score_percentage >= 70:
            return "B"
        elif score_percentage >= 60:
            return "C"
        else:
            return "F"
            
    async def get_user_and_check(self, user_id: int, img2_file: UploadFile):
        """
        Foydalanuvchini olish va uning yuzini saqlangan rasmga mosligini tekshirish.
        
        Args:
            user_id: Tekshiriladigan foydalanuvchi ID-si
            img2_file: Yuzni solishtirish uchun yuklangan yangi rasm fayli
            
        Raises:
            HTTPException: Agar foydalanuvchi topilmasa yoki yuz mos kelmasa
        """
        # Foydalanuvchini ma'lumotlar bazasidan qidirish
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user_data = result.scalars().first()
        
        # Foydalanuvchi mavjudligini tekshirish
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID-si {user_id} bo'lgan foydalanuvchi topilmadi"
            )
        
        # Foydalanuvchining bazada rasmi borligini tekshirish
        if not user_data.image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Foydalanuvchining bazada tekshirish uchun rasmi mavjud emas"
            )
        
        # Yuzlarni o'zaro solishtirish
        is_match = await compare_faces(
            img1=user_data.image, 
            img2_file=img2_file
        )
        
        # Agar yuzlar mos kelmasa
        if not is_match:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Foydalanuvchi yuzi bazadagi rasmga mos kelmadi"
            )