import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("NIM_API_KEY", "nvapi-test")
os.environ.setdefault("NIM_API_KEY_ENCRYPTION_KEY", "ZmFrZS1mZXJuZXQta2V5LW11c3QtYmUtMzJieXRlcz0=")

from app.database import Base, get_db
import app.models  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest.fixture(autouse=True)
def nim_env(monkeypatch):
    monkeypatch.setenv("NIM_API_KEY", "nvapi-test")


@pytest_asyncio.fixture
async def app_client():
    from app.main import app

    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    import app.database as db_module
    _original_session_local = db_module.AsyncSessionLocal
    db_module.AsyncSessionLocal = SessionLocal

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    db_module.AsyncSessionLocal = _original_session_local
    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def sync_app_client():
    from app.main import app

    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    import asyncio

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _drop():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(_create())

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    import app.database as db_module
    _original_session_local = db_module.AsyncSessionLocal
    db_module.AsyncSessionLocal = SessionLocal

    client = TestClient(app)
    yield client

    db_module.AsyncSessionLocal = _original_session_local
    app.dependency_overrides.clear()
    asyncio.run(_drop())
