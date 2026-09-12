"""create pets table

Revision ID: 731326997878
Revises:
Create Date: 2026-09-12 07:02:02.011494

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision: str = "731326997878"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


pets = sa.table(
    "pets",
    sa.column("name", sa.String),
    sa.column("category", sa.String),
    sa.column("photo_urls", ARRAY(sa.String)),
    sa.column("tags", ARRAY(sa.String)),
    sa.column("status", sa.String),
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("category", sa.String, nullable=True),
        sa.Column("photo_urls", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("tags", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("status", sa.String, nullable=False, server_default="available"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.bulk_insert(
        pets,
        [
            {
                "name": "doggie",
                "category": "Dogs",
                "photo_urls": ["https://example.com/doggie.jpg"],
                "tags": ["friendly", "puppy"],
                "status": "available",
            },
            {
                "name": "kitty",
                "category": "Cats",
                "photo_urls": ["https://example.com/kitty.jpg"],
                "tags": ["cute"],
                "status": "pending",
            },
            {
                "name": "retriever",
                "category": "Dogs",
                "photo_urls": [],
                "tags": ["trained"],
                "status": "sold",
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("pets")
