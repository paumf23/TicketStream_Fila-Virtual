
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=(settings.ENVIRONMENT == "development"),
)


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
