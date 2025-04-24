import os

HOST = 'http://127.0.0.1:8000'

DATABASE_URL = (
    f"postgresql+asyncpg://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@db:5432/{os.environ['DB_NAME']}"
)

SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
EMAIL_ACTIVATION_EXPIRE_MINUTES = 15

SENDER_EMAIL = os.environ['SENDER_EMAIL']
SENDER_EMAIL_PASSWORD = os.environ['SENDER_EMAIL_PASSWORD']
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587