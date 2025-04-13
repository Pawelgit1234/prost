import os

DATABASE_URL = f'postgresql+asyncpg://{os.environ['DB_USERNAME']}:{os.environ['DB_SECRET']} \
                @{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}'