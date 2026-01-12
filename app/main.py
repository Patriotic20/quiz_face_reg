from fastapi import FastAPI
from sqladmin import Admin
from fastapi.staticfiles import StaticFiles
import uvicorn
from modules.user.view import UserAdmin

from modules.router import router as main_router
from core.config import settings
from core.lifespan import lifespan
from core.db_helper import db_helper

main_app = FastAPI(lifespan=lifespan)
admin = Admin(main_app, db_helper.engine)

admin.add_view(UserAdmin)

# main_app = FastAPI()

main_app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")


main_app.include_router(main_router)



if __name__ == "__main__":

    uvicorn.run(
        settings.server.app_path,
        port=settings.server.port,
        host=settings.server.host,
    )