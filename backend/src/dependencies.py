from typing import Annotated

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.models import UserModel
from src.auth.utils import decode_jwt_token
from src.auth.services import get_user_by_username_or_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_jwt_token(token)
    user = get_user_by_username_or_email(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_active_current_user(current_user: Annotated[UserModel, Depends(get_current_user)]):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Inactive user'
        )
    return current_user