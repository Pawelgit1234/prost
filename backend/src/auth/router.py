from fastapi import APIRouter

from src.auth.schemas import UserLoginSchema

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/token')
async def login():
    pass

@router.post('/register')
async def register():
    pass
