import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Admin, AdminPlanCategory, AdminUserPlan
from app.utils import admin_plans


def test_assigned_plan_category_persists_and_exposes_plan():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        owner = Admin(username="v113-owner", hashed_password="x", is_sudo=True)
        target = Admin(username="v113-plan-admin", hashed_password="x", is_sudo=False)
        db.add_all([owner, target])
        db.flush()

        category = AdminPlanCategory(
            owner_admin_id=owner.id,
            name="v1.1.3 visible category",
        )
        db.add(category)
        db.flush()
        plan = AdminUserPlan(
            owner_admin_id=owner.id,
            category_id=category.id,
            name="v1.1.3 visible plan",
        )
        db.add(plan)
        db.commit()

        assert admin_plans.admin_category_ids(db, target.id) == []
        assert (
            admin_plans.effective_plans_query(db, target)
            .filter(AdminUserPlan.id == plan.id)
            .first()
            is None
        )

        admin_plans.replace_admin_categories(
            db,
            actor=owner,
            target=target,
            category_ids=[category.id],
        )
        db.commit()

        assert admin_plans.admin_category_ids(db, target.id) == [category.id]
        visible = (
            admin_plans.effective_plans_query(db, target)
            .filter(AdminUserPlan.id == plan.id)
            .one()
        )
        assert visible.id == plan.id

        admin_plans.replace_admin_categories(
            db,
            actor=owner,
            target=target,
            category_ids=[],
        )
        db.commit()

        assert admin_plans.admin_category_ids(db, target.id) == []
        assert (
            admin_plans.effective_plans_query(db, target)
            .filter(AdminUserPlan.id == plan.id)
            .first()
            is None
        )
    finally:
        db.close()
        engine.dispose()
