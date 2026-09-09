import inspect

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.db import crud
from app.db.base import Base
from app.db.models import Admin as DBAdmin, AdminMoneyTransaction, MarzhelpAdminSettings, User
from app.models.admin import Admin as APIAdmin, AdminCreate, AdminDeleteRequest, MarzhelpAdminPolicy
from app.models.user import UserStatus
from app.routers import admin as admin_router


def _request(username: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "DELETE",
            "path": f"/api/admin/{username}",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
            "scheme": "http",
        }
    )


def test_delete_route_retires_admin_with_nonzero_accounting_state(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'v115-admin-delete.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        actor = crud.create_admin(
            db,
            AdminCreate(username="owner-delete-test", password="secret", is_sudo=True),
        )
        target = crud.create_admin(
            db,
            AdminCreate(username="retire-with-credit", password="secret", is_sudo=False),
        )
        owned_user = User(
            username="retire-owned-user",
            admin_id=target.id,
            status=UserStatus.active,
        )
        db.add(owned_user)
        settings = crud.upsert_marzhelp_admin_policy(
            db,
            target.id,
            MarzhelpAdminPolicy(
                total_traffic=100 * 1024**3,
                calculate_volume="created_traffic",
            ),
        )
        settings.used_traffic = 40 * 1024**3
        settings.delegated_traffic = 5 * 1024**3
        settings.money_balance_toman = 250_000
        db.add(
            AdminMoneyTransaction(
                operation_key="v115-delete-history",
                operation_type="grant",
                admin_id=target.id,
                actor_admin_id=actor.id,
                counterparty_admin_id=actor.id,
                delta_toman=250_000,
                balance_before=0,
                balance_after=250_000,
            )
        )
        db.commit()

        monkeypatch.setattr(admin_router.admin_hierarchy, "admin_in_scope", lambda *_args, **_kwargs: True)
        monkeypatch.setattr(admin_router.admin_hierarchy, "role_code", lambda *_args, **_kwargs: "ADMIN")
        monkeypatch.setattr(admin_router.AuditLogService, "log", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(admin_router.xray.config, "include_db_users", lambda: {})

        class _StoppedCore:
            started = False

        monkeypatch.setattr(admin_router.xray, "core", _StoppedCore())
        monkeypatch.setattr(admin_router.xray, "nodes", {})

        response = admin_router.remove_admin(
            request=_request(target.username),
            values=AdminDeleteRequest(strategy="keep_users"),
            dbadmin=target,
            db=db,
            current_admin=APIAdmin.model_validate(actor),
        )

        assert response == {"detail": "Admin removed successfully"}
        assert crud.get_admin(db, target.username) is None
        tombstone = db.query(DBAdmin).filter(DBAdmin.username == target.username).one()
        assert tombstone.deleted_at is not None
        assert tombstone.hashed_password == ""
        assert tombstone.is_sudo is False
        assert db.get(MarzhelpAdminSettings, tombstone.id) is None
        assert db.query(User).filter(User.username == owned_user.username).one().admin_id is None
        assert db.query(AdminMoneyTransaction).filter(
            AdminMoneyTransaction.operation_key == "v115-delete-history"
        ).count() == 1
    finally:
        db.close()
        engine.dispose()


def test_delete_route_no_longer_blocks_accounting_balances():
    source = inspect.getsource(admin_router.remove_admin)
    assert "admin_delete_credit_unsettled" not in source
    assert "money_balance_toman" not in source
    assert "own_credit_spend" not in source
    assert "admin_delete_has_children" in source
    assert "admin_delete_owner_or_self_forbidden" in source
