from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from secrets import token_urlsafe

from redis.asyncio import Redis
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import aiosmtplib
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from src.settings import SECRET_KEY, ALGORITHM, \
    SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_EMAIL_PASSWORD, \
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, HTTPS, \
    REDIS_GOOGLE_STATE_KEY, GOOGLE_STATE_LIFETIME
from src.auth.schemas import TokenDataSchema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_jwt_token(
    data: dict,
    expires_delta: timedelta
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token(data: dict) -> str:
    return create_jwt_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(data: dict) -> str:
    return create_jwt_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

def create_token_response(
    access_token: str,
    refresh_token: str,
    user: dict | None = None
) -> JSONResponse:
    """ access token -> json, refresh token -> cookie & httponly """
    content = {
        "access_token": access_token,
        "token_type": "bearer"
    }

    if user is not None:
        content['user'] = user
    
    response = JSONResponse(content=content)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=HTTPS,
        samesite="lax",
        max_age=60*60*24*REFRESH_TOKEN_EXPIRE_DAYS
    )

    return response

def decode_jwt_token(token: str) -> TokenDataSchema:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        
        if username is None:
            raise credentials_exception
        token_data = TokenDataSchema(username=username)
    except InvalidTokenError:
        raise credentials_exception
    
    return token_data

async def send_html_email(to_email: str, subject: str, text: str) -> None:
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(text, 'html'))
    
    await aiosmtplib.send(
        msg,
        hostname=SMTP_SERVER,
        port=SMTP_PORT,
        username=SENDER_EMAIL,
        password=SENDER_EMAIL_PASSWORD
    )

async def create_state(r: Redis) -> str:
    state = token_urlsafe(16)
    await r.setex(REDIS_GOOGLE_STATE_KEY.format(state), GOOGLE_STATE_LIFETIME, "1")
    return state

async def validate_state(r: Redis, state: str) -> bool:
    key = REDIS_GOOGLE_STATE_KEY.format(state)
    exists = await r.get(key)

    if exists:
        await r.delete(key)
        return True
    return False
    