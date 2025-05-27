from fastapi import APIRouter

import src.auth.router
import src.chats.router

main_router = APIRouter()
main_router.include_router(src.chats.router.router)
main_router.include_router(src.auth.router.router)
