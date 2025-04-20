from typing import Annotated
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import create_acces_token
from src.auth.schemas import UserSchema, TokenSchema
from src.auth.services import authenticate_user
from src.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/token')
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    # username can be also email
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_acces_token({'sub': user.username})
    logging.info(f'{user.username} logged in')

    return TokenSchema(access_token=access_token, token_type='bearer')

@router.post('/register')
async def register():
    pass
