# AI Office — Chunk 1: Backend Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up FastAPI backend with PostgreSQL, async SQLAlchemy, JWT auth, API-key vault, rate limiting, and security headers — production-ready foundation all other chunks build on.

**Architecture:** FastAPI app with async SQLAlchemy 2.0 + PostgreSQL. Auth via JWT (python-jose). NIM API keys encrypted at rest with Fernet. Rate limiting via slowapi. Security headers injected by Starlette middleware.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic, python-jose[cryptography], passlib[bcrypt], slowapi, cryptography, pydantic-settings, pytest-asyncio, httpx

---

## File Map

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, middleware wiring, router includes
│   ├── config.py                # Pydantic Settings — reads .env
│   ├── database.py              # Async engine, session factory, Base
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User ORM
│   │   ├── task.py              # Task ORM
│   │   ├── approval_step.py     # ApprovalStep ORM
│   │   └── audit_log.py        # AuditLog ORM
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py              # LoginRequest, TokenResponse, UserOut
│   │   ├── task.py              # TaskCreate, TaskOut, TaskStatus enum
│   │   └── approval.py          # ApprovalStepOut
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # get_db, get_current_user
│   │   └── auth.py              # POST /auth/login, POST /auth/refresh
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # create_token, verify_token, hash_pw, verify_pw
│   │   └── audit_service.py     # log_action
│   └── security/
│       ├── __init__.py
│       ├── api_key_vault.py     # Fernet encrypt/decrypt NIM keys
│       ├── rate_limiter.py      # slowapi limiter instance
│       └── headers.py           # SecurityHeadersMiddleware
├── migrations/
│   ├── env.py                   # Alembic async env
│   └── alembic.ini
├── tests/
│   ├── conftest.py              # fixtures: async test DB, client, mock user
│   ├── test_auth.py
│   ├── test_api_key_vault.py
│   └── test_rate_limiter.py
├── requirements.txt
├── .env.example
└── Dockerfile
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`

- [ ] **Step 1: Write requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
slowapi==0.1.9
cryptography==42.0.5
httpx==0.27.0
celery[redis]==5.3.6
redis==5.0.4
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-cov==5.0.0
```

- [ ] **Step 2: Write .env.example**

```ini
DATABASE_URL=postgresql+asyncpg://office:office@localhost:5432/office
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=change-me-32-chars-minimum-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
NIM_API_KEY_ENCRYPTION_KEY=      # 32-byte Fernet key — generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
CORS_ORIGINS=http://localhost:5173
```

- [ ] **Step 3: Create empty __init__.py**

```bash
touch backend/app/__init__.py backend/app/models/__init__.py backend/app/schemas/__init__.py backend/app/api/__init__.py backend/app/services/__init__.py backend/app/security/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt backend/.env.example backend/app/
git commit -m "chore: bootstrap backend structure and deps"
```

---

## Task 2: Config & Database

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Test: `backend/tests/conftest.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_config.py
from app.config import settings

def test_settings_load():
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_EXPIRE_MINUTES > 0
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd backend && python -m pytest tests/test_config.py -v
# Expected: ModuleNotFoundError: No module named 'app.config'
```

- [ ] **Step 3: Write app/config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://office:office@localhost:5432/office"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "dev-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    NIM_API_KEY_ENCRYPTION_KEY: str = ""
    NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = {"env_file": ".env"}

settings = Settings()
```

- [ ] **Step 4: Write app/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 5: Run — expect PASS**

```bash
python -m pytest tests/test_config.py -v
# Expected: PASSED
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/config.py backend/app/database.py backend/tests/test_config.py
git commit -m "feat: config and async database session"
```

---

## Task 3: ORM Models

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/task.py`
- Create: `backend/app/models/approval_step.py`
- Create: `backend/app/models/audit_log.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_models.py
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.approval_step import ApprovalStep, StepStatus
from app.models.audit_log import AuditLog

def test_user_model_columns():
    cols = [c.name for c in User.__table__.columns]
    assert "id" in cols
    assert "email" in cols
    assert "hashed_password" in cols
    assert "is_owner" in cols

def test_task_status_values():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.IN_PROGRESS == "in_progress"
    assert TaskStatus.APPROVED == "approved"
    assert TaskStatus.REJECTED == "rejected"

def test_approval_step_columns():
    cols = [c.name for c in ApprovalStep.__table__.columns]
    assert "step_number" in cols
    assert "agent_role" in cols
    assert "output" in cols
    assert "status" in cols
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/test_models.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Write app/models/user.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: Write app/models/task.py**

```python
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class TaskStatus(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)  # "frontend", "backend", "devops", "full"
    status: Mapped[str] = mapped_column(String(50), default=TaskStatus.PENDING)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    celery_task_id: Mapped[str | None] = mapped_column(String, nullable=True)
```

- [ ] **Step 5: Write app/models/approval_step.py**

```python
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class StepStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"

class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_role: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=StepStatus.PENDING)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)   # APPROVE/REVISE/REJECT
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 6: Write app/models/audit_log.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    resource: Mapped[str] = mapped_column(String(200), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 7: Update models/__init__.py**

```python
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.approval_step import ApprovalStep, StepStatus
from app.models.audit_log import AuditLog

__all__ = ["User", "Task", "TaskStatus", "ApprovalStep", "StepStatus", "AuditLog"]
```

- [ ] **Step 8: Run — expect PASS**

```bash
python -m pytest tests/test_models.py -v
# Expected: 3 PASSED
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/
git commit -m "feat: ORM models — User, Task, ApprovalStep, AuditLog"
```

---

## Task 4: Alembic Migrations

**Files:**
- Create: `backend/migrations/env.py`
- Create: `backend/alembic.ini`

- [ ] **Step 1: Init alembic**

```bash
cd backend && alembic init migrations
```

- [ ] **Step 2: Replace migrations/env.py**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.config import settings
from app.database import Base
import app.models  # noqa: F401 — import all models so Base.metadata knows them

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 3: Generate first migration**

```bash
alembic revision --autogenerate -m "initial schema"
# Expected: Generating .../migrations/versions/xxxx_initial_schema.py
```

- [ ] **Step 4: Run migration against test DB**

```bash
alembic upgrade head
# Expected: Running upgrade -> xxxx, initial schema
```

- [ ] **Step 5: Commit**

```bash
git add backend/migrations/ backend/alembic.ini
git commit -m "feat: alembic async migrations — initial schema"
```

---

## Task 5: Auth Service

**Files:**
- Create: `backend/app/services/auth_service.py`
- Test: `backend/tests/test_auth_service.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_auth_service.py
import pytest
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token

def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False

def test_create_and_decode_token():
    token = create_access_token({"sub": "user-123", "is_owner": True})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["is_owner"] is True

def test_decode_invalid_token():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("not.a.real.token")
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/test_auth_service.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Write app/services/auth_service.py**

```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/test_auth_service.py -v
# Expected: 3 PASSED
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/auth_service.py backend/tests/test_auth_service.py
git commit -m "feat: auth service — bcrypt + JWT"
```

---

## Task 6: Auth Schemas + API Route

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/auth.py`
- Test: `backend/tests/test_auth_api.py`

- [ ] **Step 1: Write schemas/auth.py**

```python
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    email: str
    is_owner: bool
```

- [ ] **Step 2: Write api/deps.py**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.services.auth_service import decode_access_token
from app.models.user import User

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

async def require_owner(user: User = Depends(get_current_user)) -> User:
    if not user.is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return user
```

- [ ] **Step 3: Write api/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.auth_service import verify_password, create_access_token, hash_password
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.id, "is_owner": user.is_owner})
    await log_action(db, user_id=user.id, action="LOGIN", resource="auth", ip=request.client.host)
    return TokenResponse(access_token=token)

@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email, hashed_password=hash_password(body.password), is_owner=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut(id=user.id, email=user.email, is_owner=user.is_owner)
```

- [ ] **Step 4: Write services/audit_service.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

async def log_action(db: AsyncSession, action: str, resource: str, user_id: str | None = None, detail: str | None = None, ip: str | None = None):
    entry = AuditLog(user_id=user_id, action=action, resource=resource, detail=detail, ip_address=ip)
    db.add(entry)
    await db.commit()
```

- [ ] **Step 5: Write failing test**

```python
# backend/tests/test_auth_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/auth/register", json={"email": "owner@test.com", "password": "secret123"})
        assert r.status_code == 201
        assert r.json()["is_owner"] is True

        r2 = await client.post("/auth/login", json={"email": "owner@test.com", "password": "secret123"})
        assert r2.status_code == 200
        assert "access_token" in r2.json()

@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/auth/login", json={"email": "owner@test.com", "password": "wrong"})
        assert r.status_code == 401
```

- [ ] **Step 6: Write app/main.py (minimal, wires auth router)**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.auth import router as auth_router
from app.security.headers import SecurityHeadersMiddleware
from app.security.rate_limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI(title="AI Office", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api")
```

- [ ] **Step 7: Write conftest.py (test DB setup)**

```python
# backend/tests/conftest.py
import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base

TEST_DB_URL = "postgresql+asyncpg://office:office@localhost:5432/office_test"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def create_test_tables():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
```

- [ ] **Step 8: Run — expect PASS**

```bash
python -m pytest tests/test_auth_api.py -v
# Expected: 2 PASSED
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: auth API — register, login, JWT guard, audit log"
```

---

## Task 7: Security — API Key Vault

**Files:**
- Create: `backend/app/security/api_key_vault.py`
- Test: `backend/tests/test_api_key_vault.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_api_key_vault.py
import os
from cryptography.fernet import Fernet
from app.security.api_key_vault import encrypt_key, decrypt_key, get_nim_api_key

def test_encrypt_decrypt_roundtrip():
    raw = "nvapi-supersecret-abc123"
    enc = encrypt_key(raw)
    assert enc != raw
    assert decrypt_key(enc) == raw

def test_get_nim_api_key_reads_env(monkeypatch):
    monkeypatch.setenv("NIM_API_KEY", "nvapi-test-key")
    assert get_nim_api_key() == "nvapi-test-key"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/test_api_key_vault.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Write app/security/api_key_vault.py**

```python
import os
from cryptography.fernet import Fernet
from app.config import settings

def _fernet() -> Fernet:
    key = settings.NIM_API_KEY_ENCRYPTION_KEY
    if not key:
        # Generate ephemeral key for dev — NEVER use in prod
        return Fernet(Fernet.generate_key())
    return Fernet(key.encode() if isinstance(key, str) else key)

def encrypt_key(raw: str) -> str:
    return _fernet().encrypt(raw.encode()).decode()

def decrypt_key(encrypted: str) -> str:
    return _fernet().decrypt(encrypted.encode()).decode()

def get_nim_api_key() -> str:
    """Read NIM API key from env. Encrypted storage optional via NIM_API_KEY_ENCRYPTED."""
    encrypted = os.getenv("NIM_API_KEY_ENCRYPTED")
    if encrypted:
        return decrypt_key(encrypted)
    raw = os.getenv("NIM_API_KEY", "")
    if not raw:
        raise EnvironmentError("NIM_API_KEY or NIM_API_KEY_ENCRYPTED must be set")
    return raw
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/test_api_key_vault.py -v
# Expected: 2 PASSED
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/security/api_key_vault.py backend/tests/test_api_key_vault.py
git commit -m "feat: API key vault — Fernet encrypt/decrypt NIM keys"
```

---

## Task 8: Rate Limiter + Security Headers

**Files:**
- Create: `backend/app/security/rate_limiter.py`
- Create: `backend/app/security/headers.py`
- Test: `backend/tests/test_security.py`

- [ ] **Step 1: Write app/security/rate_limiter.py**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
```

- [ ] **Step 2: Write app/security/headers.py**

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response
```

- [ ] **Step 3: Write failing test**

```python
# backend/tests/test_security.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_security_headers_present():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/auth/login")  # 405 but headers still set
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert r.headers.get("strict-transport-security") is not None
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/test_security.py -v
# Expected: PASSED
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/security/ backend/tests/test_security.py
git commit -m "feat: rate limiter (60/min) + security headers middleware"
```

---

## Task 9: Dockerfile + Health Check

**Files:**
- Create: `backend/Dockerfile`
- Modify: `backend/app/main.py` (add /health route)

- [ ] **Step 1: Add /health route to main.py**

```python
# Add to app/main.py after app definition:
@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-office-backend"}
```

- [ ] **Step 2: Write Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

- [ ] **Step 3: Verify build**

```bash
cd backend && docker build -t ai-office-backend .
# Expected: Successfully built ...
```

- [ ] **Step 4: Run container smoke test**

```bash
docker run --rm -p 8000:8000 -e DATABASE_URL=postgresql+asyncpg://... ai-office-backend &
sleep 3
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"ai-office-backend"}
```

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/app/main.py
git commit -m "feat: Dockerfile + /health endpoint"
```

---

## Chunk 1 Complete

All tasks done when:
- `pytest backend/tests/ -v` → all green
- `docker build backend/` → success
- `/health` returns 200
- Auth register + login flow works end-to-end

**Next:** Chunk 2 — Agent Layer (NIM integrations for all 11 roles)
