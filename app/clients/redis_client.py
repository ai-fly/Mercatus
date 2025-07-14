from redis import Redis
from app.config import settings


class RedisClient:
    def __init__(self):
        self.redis_client = Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)

    def get_redis_client(self) -> Redis:
        return self.redis_client
    

redis_client_instance = RedisClient()