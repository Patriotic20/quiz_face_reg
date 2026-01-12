from fastapi import FastAPI
from contextlib import asynccontextmanager


from core.utils.dependencies import sync_permissions_to_db
from core.utils.base_roles import create_roles
from core.utils.assign_user_roles import setup_admin_user
from core.utils.redis_helper import init_redis_services
from core.logging import logging
from core.db_helper import db_helper
from core.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    
    redis_conn = None
    
    try:
        # Вызов вашей новой функции
        redis_conn = await init_redis_services(settings.redis.url)
        logger.info("Redis services initialized.")

        # Остальные задачи
        await sync_permissions_to_db()
        await create_roles()
        await setup_admin_user()
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if redis_conn:
        await redis_conn.close()
    await db_helper.dispose()