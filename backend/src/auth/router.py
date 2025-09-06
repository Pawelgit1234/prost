from typing import Annotated
from uuid import uuid4, UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, \
    Request, Cookie, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth

from src.database import get_db
from src.utils import save_to_db, get_object_or_404
from src.dependencies import get_current_user
from src.settings import HOST, GOOGLE_CLIENT_SECRET, GOOGLE_CLIENT_ID
from src.auth.utils import create_access_token, create_refresh_token, send_html_email, \
    decode_jwt_token, create_token_response
from src.auth.schemas import UserRegisterSchema, UserSchema
from src.auth.services import authenticate_user, create_user, create_email_activation_token, \
    activate_user 
from src.auth.models import UserModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['auth'])

oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

@router.get('/google/login')
async def google_login(request: Request):
    redirect_url = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_url)

@router.get('/google/callback')
async def google_callback(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    token = await oauth.google.authorize_access_token(request)
    resp = await oauth.google.get('userinfo', token=token)
    user_info = resp.json()

    user = await get_object_or_404(
        db, UserModel,
        UserModel.email == user_info['email'], detail='User not found'
    )

    if user is None:
        username = ('_'.join(user_info['name'].split()).lower() + str(uuid4()))[:16]
        new_user = UserModel(
            first_name=user_info['given_name'],
            last_name=user_info['family_name'],
            username=username,
            email=user_info['email'],
            avatar=user_info['picture'],
            is_active=user_info['verified_email']
        )
        user = (await save_to_db(db, [new_user]))[0]

        logging.info(f'{user.username} registered in by google')
    else:
        logging.info(f'{user.username} logged in by google')

    access_token = create_access_token({'sub': user.username})
    refresh_token = create_refresh_token({'sub': user.username})
    return create_token_response(access_token, refresh_token)

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
    access_token = create_access_token({'sub': user.username})
    refresh_token = create_refresh_token({'sub': user.username})
    user_dict = UserSchema.model_validate(user).model_dump(mode='json')

    return create_token_response(access_token, refresh_token, user_dict)

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
    access_token = create_access_token({'sub': user.username})
    refresh_token = create_refresh_token({'sub': user.username})
    return create_token_response(access_token, refresh_token)

@router.get('/activation/{email_activation_token}')
async def activate(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    email_activation_token: UUID
):
    await activate_user(db, email_activation_token, user)
    logging.info(f'{user.username} was activated')
    return {'success': True}

@router.post('/refresh')
async def get_refresh_token(refresh_token: str | None = Cookie(default=None)):
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    token_data = decode_jwt_token(refresh_token)

    # new access and refresh token
    access_token = create_access_token({'sub': token_data.username})
    refresh_token = create_refresh_token({'sub': token_data.username})
    return create_token_response(access_token, refresh_token)

@router.post('/logout')
async def logout(reponse: Response):
    reponse.delete_cookie('refresh_token')
    return {'success': True}