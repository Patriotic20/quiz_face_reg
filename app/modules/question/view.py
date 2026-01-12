from sqladmin import ModelView
from models.questions import Question

class QuestionAdmin(ModelView, model=Question):
    column_list = [
        Question.id, 
        Question.text, 
        Question.option_a, 
        Question.option_b, 
        Question.option_c, 
        Question.option_d, 
        Question.created_at, 
        Question.updated_at,
        Question.quiz_id,
    ] 
    column_searchable_list = [
        Question
    ]