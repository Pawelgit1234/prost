import os

HOST = 'http://127.0.0.1:8000'

DATABASE_URL = (
    f"postgresql+asyncpg://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@db:5432/{os.environ['DB_NAME']}"
)

INVITATION_CLEANING_SLEEP_TIME = 5 * 60 # 5 minutes

REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_CACHE_EXPIRE_SECONDS = 60 * 60 # 1 hour
REDIS_FOLDERS_KEY = 'folders_{}' # 'folders_{user_uuid}'
REDIS_CHATS_KEY = 'chats_{}_{}' # 'chats_{folder_uuid}_{user_uuid}'
REDIS_USER_JOIN_REQUESTS_KEY = 'user_join_requests_{}' # 'user_join_requests_{user_uuid}'
REDIS_GROUP_JOIN_REQUESTS_KEY = 'group_join_requests_{}' # 'group_join_requests_{group_uuid}'
REDIS_USER_INVITATION_KEY = 'user_invitation_{}' # 'user_invitation_{user_uuid}'
REDIS_GROUP_INVITATION_KEY = 'group_invitation_{}' # 'group_invitation_{group_uuid}'
REDIS_SEARCH_HISTORY_KEY = 'search_history_{}' # 'history_{user_uuid}'
SEARCH_HISTORY_SIZE = 100

ELASTIC_HOST = 'http://elasticsearch:9200'
ELASTIC_PASSWORD = os.environ['ELASTIC_PASSWORD']
ELASTIC_CHATS_INDEX_NAME = 'chats'
ELASTIC_USERS_INDEX_NAME = 'users'
ELASTIC_MESSAGES_INDEX_NAME = 'messages'
ELASTIC_PAGE_SIZE = 20

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
