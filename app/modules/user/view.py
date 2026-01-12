from sqladmin import ModelView
from models.user import User

class UserAdmin(ModelView, model=User):
    # Список полей для отображения в таблице (Password сюда не включаем)
    column_list = [
        User.id,
        User.username, # Рекомендую добавить, чтобы видеть логин
        User.first_name,
        User.last_name,
        User.third_name,
        User.roles,
        User.created_at,
    ]
    
    column_searchable_list = [
        User.username, 
        User.first_name, 
        User.last_name,
    ]
    
    column_filters = [
        User.roles,      # Ссылка на поле через класс
        User.created_at  # Ссылка на поле через класс
    ]
    
    # Поля, которые будут в форме создания/редактирования
    form_columns = [
        "username",
        "password",
        "first_name",
        "last_name",
        "third_name",
        "jshir",
        "passport_series",
        "roles",   
        "image",
    ]
    
    # УДАЛЕНО: column_exclude_list (нельзя использовать вместе с column_list)
    
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    
    form_ajax_refs = {
        "roles": {
            "fields": ("name",), 
        }
    }