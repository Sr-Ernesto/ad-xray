import asyncpg
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from api.config import get_settings

settings = get_settings()

# SQLAlchemy sync for standard API routes
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# asyncpg for fast worker operations
pool: asyncpg.Pool | None = None

async def init_db_pool():
    global pool
    pool = await asyncpg.create_pool(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
    )

async def close_db_pool():
    global pool
    if pool:
        await pool.close()

@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    if not pool:
        await init_db_pool()
    
    async with pool.acquire() as connection:
        yield connection

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
