from src.auth.models import UserModel
from src.auth.schemas import UserRegisterSchema
from src.auth.services import create_user

async def create_user1(db) -> UserModel:
    user1 = await create_user(db, UserRegisterSchema(
        first_name='User',
        last_name='One',
        username='user1',
        description='desc',
        email='user1@example.com',
        password='Secret12%8800'
    ))
    return user1

async def create_user2(db) -> UserModel:
    user2 = await create_user(db, UserRegisterSchema(
        first_name='User',
        last_name='Two',
        username='user2',
        description='desc',
        email='user2@example.com',
        password='Secret12%8800'
    ))
    return user2