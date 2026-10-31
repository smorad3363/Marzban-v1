"""Durable active incidents and separate per-viewer receipts."""
from alembic import op
import sqlalchemy as sa

revision = 'c7f3a1d9e820'
down_revision = 'b6e2c9f4a810'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if not sa.inspect(bind).has_table('admin_alert_incidents'):
        op.create_table('admin_alert_incidents',
            sa.Column('id',sa.Integer(),primary_key=True,autoincrement=True),
            sa.Column('admin_id',sa.Integer(),sa.ForeignKey('admins.id',ondelete='CASCADE'),nullable=False),
            sa.Column('resource',sa.String(32),nullable=False),
            sa.Column('state',sa.String(32),nullable=False),
            sa.Column('severity',sa.String(16),nullable=False),
            sa.Column('details',sa.JSON(),nullable=False),
            sa.Column('revision',sa.Integer(),nullable=False),
            sa.Column('opened_at',sa.DateTime(),nullable=False),
            sa.Column('updated_at',sa.DateTime(),nullable=False),
            sa.Column('resolved_at',sa.DateTime(),nullable=True),
            sa.UniqueConstraint('admin_id','resource',name='uq_admin_incident_resource'))
    indexes = {i['name'] for i in sa.inspect(bind).get_indexes('admin_alert_incidents')}
    if 'ix_admin_alert_incidents_admin_id' not in indexes:
        op.create_index('ix_admin_alert_incidents_admin_id','admin_alert_incidents',['admin_id'])
    if 'ix_admin_incident_active' not in indexes:
        op.create_index('ix_admin_incident_active','admin_alert_incidents',['resolved_at','severity','admin_id','id'])
    if not sa.inspect(bind).has_table('admin_alert_receipts'):
        op.create_table('admin_alert_receipts',
            sa.Column('viewer_admin_id',sa.Integer(),sa.ForeignKey('admins.id',ondelete='CASCADE'),primary_key=True),
            sa.Column('incident_id',sa.Integer(),sa.ForeignKey('admin_alert_incidents.id',ondelete='CASCADE'),primary_key=True),
            sa.Column('revision',sa.Integer(),nullable=False),
            sa.Column('seen_at',sa.DateTime(),nullable=False))
    if not sa.inspect(bind).has_table('admin_alert_scan_state'):
        op.create_table('admin_alert_scan_state',sa.Column('id',sa.Integer(),primary_key=True),
                        sa.Column('checked_at',sa.DateTime(),nullable=False))


def downgrade():
    for name in ('admin_alert_scan_state', 'admin_alert_receipts', 'admin_alert_incidents'):
        op.drop_table(name)
