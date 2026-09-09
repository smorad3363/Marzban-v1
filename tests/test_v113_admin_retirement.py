from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import crud
from app.db.base import Base
from app.db.models import Admin, AdminMoneyTransaction, User
from app.models.admin import AdminCreate
from app.models.user import UserStatus


def test_admin_retirement_preserves_immutable_money_history_and_hides_account(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'v113-retire.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        admin = crud.create_admin(
            db, AdminCreate(username="retire-me", password="secret", is_sudo=False)
        )
        user = User(username="retired-user", admin_id=admin.id, status=UserStatus.active)
        db.add(user)
        db.add(AdminMoneyTransaction(
            operation_key="v113-history", operation_type="grant",
            admin_id=admin.id, actor_admin_id=admin.id, counterparty_admin_id=None,
            delta_toman=1000, balance_before=0, balance_after=1000,
        ))
        db.commit()

        assert crud.remove_admin(db, admin, "keep_users") == 1
        assert crud.get_admin(db, "retire-me") is None
        tombstone = db.query(Admin).filter(Admin.username == "retire-me").one()
        assert tombstone.deleted_at is not None
        assert tombstone.parent_admin_id is None
        assert db.query(AdminMoneyTransaction).filter(
            AdminMoneyTransaction.operation_key == "v113-history"
        ).count() == 1
        assert db.query(User).filter(User.username == "retired-user").one().admin_id is None
        admins, total = crud.get_admins_with_count(db)
        assert total == 0
        assert admins == []
    finally:
        db.close()
        engine.dispose()
