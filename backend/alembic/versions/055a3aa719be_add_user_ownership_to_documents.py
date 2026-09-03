"""add user ownership to documents

Revision ID: 055a3aa719be
Revises: b3cdfff248dc
Create Date: 2026-08-09 12:20:08.657680

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "055a3aa719be"
down_revision: Union[str, Sequence[str], None] = "b3cdfff248dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------
    # 1. Add user_id temporarily as nullable
    # --------------------------------------------------

    op.add_column(
        "documents",
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True
        )
    )

    # --------------------------------------------------
    # 2. Assign existing documents to user ID 1
    # --------------------------------------------------

    op.execute(
        "UPDATE documents SET user_id = 1 WHERE user_id IS NULL"
    )

    # --------------------------------------------------
    # 3. Make user_id mandatory
    # --------------------------------------------------

    op.alter_column(
        "documents",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    # --------------------------------------------------
    # 4. Create foreign key
    # --------------------------------------------------

    op.create_foreign_key(
        "fk_documents_user_id_users",
        "documents",
        "users",
        ["user_id"],
        ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_documents_user_id_users",
        "documents",
        type_="foreignkey"
    )

    op.drop_column(
        "documents",
        "user_id"
    )