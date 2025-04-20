from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')

async def get_current_user():
    pass

async def get_current_active_user():
    pass