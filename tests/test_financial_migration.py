import importlib.util
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_financial_migration_replay_and_latest_grant_basis():
    path='app/db/migrations/versions/f31a6c9d2e70_add_financial_controls.py'
    spec=importlib.util.spec_from_file_location('financial_migration',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    engine=sa.create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(sa.text('CREATE TABLE admins (id INTEGER PRIMARY KEY)'))
        connection.execute(sa.text('CREATE TABLE users (id INTEGER PRIMARY KEY)'))
        connection.execute(sa.text('CREATE TABLE marzhelp_admin_settings (admin_id INTEGER PRIMARY KEY)'))
        connection.execute(sa.text('CREATE TABLE admin_money_transactions (id INTEGER PRIMARY KEY, admin_id INTEGER, operation_type TEXT, delta_toman BIGINT)'))
        connection.execute(sa.text('INSERT INTO admins VALUES (1)'))
        connection.execute(sa.text('INSERT INTO marzhelp_admin_settings VALUES (1)'))
        connection.execute(sa.text("INSERT INTO admin_money_transactions VALUES (1,1,'grant',1000),(2,1,'grant',2000),(3,1,'purchase_refund',5000)"))
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade();module.upgrade()
        row=connection.execute(sa.text('SELECT last_positive_charge_toman,financial_freeze_percent,financial_disable_percent,financial_limits_enabled FROM marzhelp_admin_settings')).one()
        assert tuple(row)==(2000,10,40,1)
        assert {'user_deletion_requests','admin_account_alerts','admin_financial_user_holds'}<=set(sa.inspect(connection).get_table_names())
