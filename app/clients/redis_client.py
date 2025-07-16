from redis import Redis
from app.config import settings


class RedisClient:
    def __init__(self):
        self.redis_client = Redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            db=settings.redis_db,
            max_connections=settings.redis_max_connections,
            socket_timeout=settings.redis_timeout
        )

    def get_redis_client(self) -> Redis:
        return self.redis_client
    

redis_client_instance = RedisClient()