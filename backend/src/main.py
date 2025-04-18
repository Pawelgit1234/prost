from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from src.routers import main_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(main_router)

if __name__ == '__main__':
    uvicorn.run('src.main:app', host="0.0.0.0", port=8000, reload=True)