# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base

# URL_DATABASE = 'sqlite:///./finance.db'

# engine = create_engine(URL_DATABASE, connect_args={"check_same_thread": False})

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
URL_DATABASE = 'sqlite+aiosqlite:///./finance.db' 
engine = create_async_engine(URL_DATABASE, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
