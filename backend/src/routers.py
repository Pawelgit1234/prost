from fastapi import APIRouter

import src.auth.router

main_router = APIRouter()
main_router.include_router(src.auth.router.router)
