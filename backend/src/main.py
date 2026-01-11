from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from starlette.middleware.sessions import SessionMiddleware

from src.routers import main_router
from src.settings import SECRET_KEY, FRONTEND_HOST
from src.logger import setup_logging
from src.database import create_indices, wait_for_elasticsearch, sync_db_to_elastic,\
    es, async_session
from src.invitations.background import periodic_invitation_cleaner

@asynccontextmanager
async def lifespan(app: FastAPI):
    # logging
    setup_logging()

    # elasticsearch
    await wait_for_elasticsearch(es)
    await create_indices(es)

    # async with async_session() as db:
    #     await sync_db_to_elastic(db, es)

    # invitation cleaner
    asyncio.create_task(periodic_invitation_cleaner()) # deletes old invitations
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(main_router)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY) # for google-auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run('src.main:app', host="0.0.0.0", port=8000, reload=True)
