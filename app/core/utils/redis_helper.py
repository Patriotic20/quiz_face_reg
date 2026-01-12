from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter

async def init_redis_services(redis_url: str):
    """
    Инициализация всех сервисов, зависящих от Redis.
    Возвращает объект соединения для последующего закрытия.
    """
    # Создаем подключение
    redis_connection = aioredis.from_url(
        redis_url, 
        encoding="utf8", 
        decode_responses=True
    )
    
    # Настройка кэширования
    FastAPICache.init(RedisBackend(redis_connection), prefix="fastapi-cache")
    
    # Настройка лимитера запросов
    await FastAPILimiter.init(redis_connection)
    
    return redis_connection