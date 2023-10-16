"""Fix Model Artifacts [6f707b385dc1].

Revision ID: 6f707b385dc1
Revises: 0.45.0
Create Date: 2023-10-13 11:34:55.907563

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6f707b385dc1"
down_revision = "0.45.0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema and/or data, creating a new revision."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "model_versions_artifacts", schema=None
    ) as batch_op:
        batch_op.alter_column(
            "pipeline_name",
            existing_type=sa.VARCHAR(),
            type_=sa.TEXT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "step_name",
            existing_type=sa.VARCHAR(),
            type_=sa.TEXT(),
            existing_nullable=False,
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade database schema and/or data back to the previous revision."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "model_versions_artifacts", schema=None
    ) as batch_op:
        batch_op.alter_column(
            "step_name",
            existing_type=sa.TEXT(),
            type_=sa.VARCHAR(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "pipeline_name",
            existing_type=sa.TEXT(),
            type_=sa.VARCHAR(),
            existing_nullable=False,
        )

    # ### end Alembic commands ###