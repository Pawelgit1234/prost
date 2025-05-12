import sys

sys.path.append('/app')

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient

from src.database import Base
from src.auth.models import *
from src.chats.models import *
from src.folders.models import *
from src.main import app

DATABASE_URL = 'sqlite+aiosqlite:///:memory:'

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

@pytest_asyncio.fixture
async def get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as client:
        yield client
