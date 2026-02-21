from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from dotenv import load_dotenv
import os
from app.db.base import Base


load_dotenv()

DB_URL = os.getenv("DB_URL")
if DB_URL is None:
    raise ValueError("DB_URL not set in environment")

engine = create_async_engine(
    DB_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=True,
    connect_args={"ssl": True},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
