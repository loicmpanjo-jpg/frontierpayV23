"""Pytest Configuration"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://fp:fp@localhost/frontierpay_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestSession() as session:
        yield session
        await session.rollback()
