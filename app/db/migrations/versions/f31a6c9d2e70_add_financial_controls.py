"""Persistent financial controls, deletion approvals and scoped alerts."""
from alembic import op
import sqlalchemy as sa

revision = "f31a6c9d2e70"
down_revision = "b01ec26a4d50"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {c['name'] for c in sa.inspect(bind).get_columns('marzhelp_admin_settings')}
    fields = [
        sa.Column('last_positive_charge_toman', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('financial_limits_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('financial_freeze_percent', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('financial_disable_percent', sa.Integer(), nullable=False, server_default='40'),
        sa.Column('financial_state', sa.String(16), nullable=False, server_default='normal'),
        sa.Column('financial_runtime_revision', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('financial_runtime_applied_revision', sa.BigInteger(), nullable=False, server_default='0'),
    ]
    for column in fields:
        if column.name not in columns:
            op.add_column('marzhelp_admin_settings', column)
    # Only a wallet grant establishes the basis. Refunds and resale revenue do not.
    bind.execute(sa.text("""UPDATE marzhelp_admin_settings SET last_positive_charge_toman = COALESCE(
        (SELECT delta_toman FROM admin_money_transactions t
         WHERE t.admin_id = marzhelp_admin_settings.admin_id
         AND t.operation_type = 'grant' AND t.delta_toman > 0
         ORDER BY t.id DESC LIMIT 1), 0) WHERE last_positive_charge_toman = 0"""))
    tables = set(sa.inspect(bind).get_table_names())
    if 'user_deletion_requests' not in tables:
        op.create_table('user_deletion_requests',
            sa.Column('id',sa.Integer(),primary_key=True,autoincrement=True),
            sa.Column('user_id',sa.Integer(),nullable=False),
            sa.Column('username',sa.String(34),nullable=False),
            sa.Column('account_admin_id',sa.Integer(),sa.ForeignKey('admins.id',ondelete='RESTRICT'),nullable=False),
            sa.Column('requester_admin_id',sa.Integer(),sa.ForeignKey('admins.id',ondelete='RESTRICT'),nullable=False),
            sa.Column('reviewer_admin_id',sa.Integer(),sa.ForeignKey('admins.id',ondelete='RESTRICT'),nullable=False),
            sa.Column('status',sa.String(16),nullable=False,server_default='PENDING'),
            sa.Column('purchase_toman',sa.BigInteger(),nullable=False,server_default='0'),
            sa.Column('refund_toman',sa.BigInteger(),nullable=True),
            sa.Column('used_bytes',sa.BigInteger(),nullable=False),
            sa.Column('quota_bytes',sa.BigInteger(),nullable=False),
            sa.Column('purchase_snapshot',sa.JSON(),nullable=False),
            sa.Column('decided_by_admin_id',sa.Integer(),nullable=True),
            sa.Column('decision_note',sa.String(512),nullable=True),
            sa.Column('created_at',sa.DateTime(),nullable=False),
            sa.Column('decided_at',sa.DateTime(),nullable=True))
    if 'admin_financial_user_holds' not in tables:
        op.create_table('admin_financial_user_holds',
            sa.Column('admin_id',sa.Integer(),sa.ForeignKey('admins.id',ondelete='CASCADE'),primary_key=True),
            sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='CASCADE'),primary_key=True),
            sa.Column('previous_status',sa.String(16),nullable=False),
            sa.Column('restore_allowed',sa.Boolean(),nullable=False,server_default=sa.true()),
            sa.Column('created_at',sa.DateTime(),nullable=False))
    if 'admin_account_alerts' not in tables:
        op.create_table('admin_account_alerts',
            sa.Column('id',sa.Integer(),primary_key=True,autoincrement=True),
            sa.Column('admin_id',sa.Integer(),sa.ForeignKey('admins.id',ondelete='CASCADE'),nullable=False),
            sa.Column('event_key',sa.String(160),nullable=False,unique=True),
            sa.Column('kind',sa.String(32),nullable=False),
            sa.Column('details',sa.JSON(),nullable=True),
            sa.Column('created_at',sa.DateTime(),nullable=False))
    for table, column in [('user_deletion_requests','user_id'),('user_deletion_requests','account_admin_id'),('user_deletion_requests','reviewer_admin_id'),('admin_account_alerts','admin_id')]:
        name = f'ix_{table}_{column}'
        if name not in {i['name'] for i in sa.inspect(bind).get_indexes(table)}:
            op.create_index(name,table,[column])


def downgrade():
    for table in ['admin_account_alerts','admin_financial_user_holds','user_deletion_requests']:
        op.drop_table(table)
    for column in ['financial_runtime_applied_revision','financial_runtime_revision','financial_state','financial_disable_percent','financial_freeze_percent','financial_limits_enabled','last_positive_charge_toman']:
        op.drop_column('marzhelp_admin_settings',column)
