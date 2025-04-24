from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import create_acces_token, send_html_email
from src.auth.schemas import TokenSchema, UserRegisterSchema
from src.auth.services import authenticate_user, create_user, create_email_activation_token, \
    activate_user
from src.auth.models import UserModel
from src.database import get_db
from src.dependencies import get_current_user
from src.settings import HOST

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

    logging.info(f'{user.username} logged in')
    access_token = create_acces_token({'sub': user.username})
    return TokenSchema(access_token=access_token, token_type='bearer')

@router.post('/register')
async def register(
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    user_data: UserRegisterSchema
):
    user = await create_user(db, user_data)
    email_activaton_token = await create_email_activation_token(db, user)
    
    # email sending is a very long operation, so I putted it in background_tasks
    activation_link = HOST + '/auth/activation/' + str(email_activaton_token.uuid)
    background_tasks.add_task(
        send_html_email,
        user_data.email,
        'Email activation',
        f"""
            Hello, thank you for registering on our site.
            Here is your email activation
            <a href={activation_link}>link</a>.
        """
    )
    
    logging.info(f'{user.username} registration completed')
    access_token = create_acces_token({'sub': user.username})
    return TokenSchema(access_token=access_token, token_type='bearer')

@router.get('/activation/{email_activation_token}')
async def activate(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    email_activation_token: str
):
    activate_user(db, email_activation_token, user)
    return {'success': True}

@router.post('/refresh_token')
async def get_refresh_token(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    pass