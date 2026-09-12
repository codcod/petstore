import os

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine

try:
    DATABASE_URL = os.environ['DATABASE_URL']
except KeyError as exc:
    raise RuntimeError(
        'DATABASE_URL is not set, e.g. postgresql+asyncpg://user:pass@host:5432/db'
    ) from exc

engine = create_async_engine(DATABASE_URL)
metadata = MetaData()
