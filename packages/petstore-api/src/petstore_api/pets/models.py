from sqlalchemy import Column, DateTime, Integer, String, Table, func
from sqlalchemy.dialects.postgresql import ARRAY

from petstore_api.db import metadata

pets = Table(
    'pets',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('category', String, nullable=True),
    Column('photo_urls', ARRAY(String), nullable=False, server_default='{}'),
    Column('tags', ARRAY(String), nullable=False, server_default='{}'),
    Column('status', String, nullable=False, server_default='available'),
    Column(
        'created_at', DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)
