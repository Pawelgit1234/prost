import os

HOST = 'http://127.0.0.1:8000'

DATABASE_URL = (
    f"postgresql+asyncpg://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@db:5432/{os.environ['DB_NAME']}"
)

REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_CACHE_EXPIRE_SECONDS = 60 * 60 # 1 hour
REDIS_FOLDERS_KEY = 'folders_{}' # 'folders_{user_uuid}'
REDIS_CHATS_KEY = 'chats_{}' # 'chats_{folder_uuid}'

SECRET_KEY = os.environ['SECRET_KEY']

GOOGLE_CLIENT_ID=os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET=os.environ['GOOGLE_CLIENT_SECRET']

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30
EMAIL_ACTIVATION_EXPIRE_MINUTES = 15

SENDER_EMAIL = os.environ['SENDER_EMAIL']
SENDER_EMAIL_PASSWORD = os.environ['SENDER_EMAIL_PASSWORD']
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587