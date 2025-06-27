from fastapi import APIRouter

import src.auth.router
import src.chats.router
import src.folders.router
import src.search.router

main_router = APIRouter()
main_router.include_router(src.auth.router.router)
main_router.include_router(src.chats.router.router)
main_router.include_router(src.folders.router.router)
main_router.include_router(src.search.router.router)
