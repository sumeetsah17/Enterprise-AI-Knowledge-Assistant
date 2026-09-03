"""add conversations and messages

Revision ID: 9ad44d3de45a
Revises: 055a3aa719be
Create Date: 2026-08-10 08:57:50.804538
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic

revision: str = "9ad44d3de45a"
down_revision: Union[str, Sequence[str], None] = "055a3aa719be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "conversations",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False
        ),

        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"]
        )
    )

    op.create_index(
        "ix_conversations_id",
        "conversations",
        ["id"]
    )


    op.create_table(
        "messages",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False
        ),

        sa.Column(
            "conversation_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            "content",
            sa.Text(),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"]
        )
    )

    op.create_index(
        "ix_messages_id",
        "messages",
        ["id"]
    )


def downgrade() -> None:

    op.drop_index(
        "ix_messages_id",
        table_name="messages"
    )

    op.drop_table("messages")

    op.drop_index(
        "ix_conversations_id",
        table_name="conversations"
    )

    op.drop_table("conversations")
