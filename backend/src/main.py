from fastapi import FastAPI
import uvicorn
from starlette.middleware.sessions import SessionMiddleware

from src.routers import main_router
from src.settings import SECRET_KEY

app = FastAPI()
app.include_router(main_router)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

if __name__ == '__main__':
    uvicorn.run('src.main:app', host="0.0.0.0", port=8000, reload=True)