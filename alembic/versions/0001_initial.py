# alembic/versions/0001_initial.py
"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-01-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(length=128), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=256), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('balance_usd', sa.Float(), nullable=True, server_default='0'),
    )
    op.create_table(
        'crypto_holdings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('wallet_id', sa.Integer(), sa.ForeignKey('wallets.id'), nullable=False),
        sa.Column('asset', sa.String(length=32), nullable=False),
        sa.Column('amount', sa.Float(), nullable=True, server_default='0'),
    )
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.String(length=50)),
        sa.Column('amount_usd', sa.Float(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'bets',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('game', sa.String(length=100)),
        sa.Column('amount_usd', sa.Float(), nullable=True),
        sa.Column('odds', sa.Float(), nullable=True),
        sa.Column('result', sa.String(length=50), nullable=True),
        sa.Column('payout', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table('bets')
    op.drop_table('transactions')
    op.drop_table('crypto_holdings')
    op.drop_table('wallets')
    op.drop_table('users')
