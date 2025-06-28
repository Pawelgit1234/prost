from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from starlette.middleware.sessions import SessionMiddleware

from src.routers import main_router
from src.settings import SECRET_KEY
from src.database import create_indices

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_indices() # elasticsearch
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(main_router)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY) # for google-auth

if __name__ == '__main__':
    uvicorn.run('src.main:app', host="0.0.0.0", port=8000, reload=True)
