import os

DATABASE_URL = (
    f"postgresql+asyncpg://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@db:5432/{os.environ['DB_NAME']}"
)