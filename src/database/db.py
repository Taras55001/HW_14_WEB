import contextlib
import redis
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.conf.config import config, redis_config


class Base(DeclarativeBase):
    pass


class DatabaseSessionManager:

    def __init__(self, url: str):
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker | None = async_sessionmaker(autocommit=False, autoflush=False,
                                                                            bind=self._engine)

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker is None:
            raise Exception("DatabaseSessionManager is not initialised")
        session = self._session_maker()
        try:
            yield session
        except Exception as error:
            print(error)
            await session.rollback()
        finally:
            session.close()


class RedisSessionManager:
    def __init__(self, r):
        self.redis = redis.Redis(host=r.host, port=r.port, password=r.password, db=0, encoding="utf-8",
                                 decode_responses=True)


sessionmanager = DatabaseSessionManager(config.DB_URL)
redis_sessionmanager = RedisSessionManager(redis_config)


# Dependency
async def get_db():
    async with sessionmanager.session() as session:
        yield session
