"""add term column

Revision ID: 4b8af9f625f6
Revises: ec9ecc731b7b
Create Date: 2024-02-05 20:10:03.872059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b8af9f625f6'
down_revision: Union[str, None] = 'ec9ecc731b7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('engineering_discipline', sa.Column('term', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('engineering_discipline', 'term')
    # ### end Alembic commands ###
