from pydantic import BaseModel, Field, field_validator
from typing import Optional

from core.schemas.time_mixin import DateTimeMixin
from core.schemas.pagination import PaginatedResponse


class QuizCreateRequest(BaseModel):
    """Test yaratish uchun so'rov modeli"""
    name: str = Field(..., min_length=1, max_length=100, description="Testning nomi")
    during: int = Field(..., gt=0, description="Test davomiyligi (daqiqalarda)")
    quiz_number: int = Field(default=0, ge=0, description="Test tartib raqami (0 dan boshlanadi)")
    pin: str = Field(..., description="Testga kirish uchun maxsus PIN-kod")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Nom bo'sh emasligini tekshirish"""
        if not v.strip():
            raise ValueError("Test nomi bo'sh bo'lishi mumkin emas")
        return v.strip()


class QuizCreate(QuizCreateRequest):
    """Ichki maydonlar bilan test yaratish modeli"""
    user_id: int = Field(..., gt=0, description="Testni yaratgan foydalanuvchi (o'qituvchi) ID-si")


class QuizResponse(DateTimeMixin):
    """Test ma'lumotlarini qaytarish uchun model"""
    id: int = Field(..., description="Testning unikal ID-si")
    name: str = Field(..., description="Test nomi")
    quiz_number: int = Field(..., description="Test tartib raqami")
    during: int = Field(..., description="Berilgan vaqt (daqiqa)")
    pin: str = Field(..., description="Kirish PIN-kodi")
    

class QuizUpdate(BaseModel):
    """Testni tahrirlash modeli - barcha maydonlar ixtiyoriy"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Yangi nom")
    during: Optional[int] = Field(None, gt=0, description="Yangi davomiylik vaqti")
    quiz_number: Optional[int] = Field(None, ge=0, description="Yangi tartib raqami")
    pin: Optional[str] = Field(None, description="Yangi PIN-kod")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Agar nom berilgan bo'lsa, uning bo'sh emasligini tekshirish"""
        if v is not None and not v.strip():
            raise ValueError("Test nomi bo'sh bo'lishi mumkin emas")
        return v.strip() if v else None
    
    
class QuizListResponse(PaginatedResponse):
    """Pagunatsiya bilan testlar ro'yxatini qaytarish modeli"""
    quizzes: list[QuizResponse] = Field(..., description="Testlar ro'yxati")


class AnswerItem(BaseModel):
    """Bitta savolga berilgan javob modeli"""
    question_id: int = Field(..., description="Savolning ID-si")
    option: str = Field(..., description="Tanlangan javob varianti")


class EndQuizCreate(BaseModel):
    """Testni yakunlash va topshirish modeli"""
    quiz_id: int = Field(..., description="Topshirilayotgan testning ID-si")
    answers: list[AnswerItem] = Field(..., description="Berilgan javoblar ro'yxati")


class QuizResultResponse(BaseModel):
    """Test topshirilgandan keyingi natija modeli"""
    quiz_id: int = Field(..., description="Test ID-si")
    total_questions: int = Field(..., description="Umumiy savollar soni")
    correct_answers: int = Field(..., description="To'g'ri javoblar soni")
    incorrect_answers: int = Field(..., description="Noto'g'ri javoblar soni")
    score_percentage: float = Field(..., description="Umumiy natija foizda")
    grade: str = Field(..., description="Baho yoki natija darajasi")