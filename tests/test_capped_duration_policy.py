from datetime import datetime, timedelta, timezone
import importlib.util

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from pydantic import ValidationError

from app.db import crud
from app.db.models import OwnerCommercialPolicy, OwnerDurationPreset, User
from app.models.admin_hierarchy import OwnerPricingUpdate
from app.models.user import UserCreate, UserModify, UserStatus
from app.utils import owner_pricing
from app.utils.marzhelp_policy import MarzhelpPolicyError
from app.utils.user_duration import require_duration
from test_stage5_restricted_creation_namespace import db as database, _network, _admin, _payload
from test_financial_controls import tree


@pytest.mark.parametrize('days,expected', [(1,10000),(30,10000),(31,10018),(60,10491),(180,11663),(365,12000),(366,12000),(5000,12000),(10**9,12000)])
def test_daily_curve_samples_and_unbounded_pricing_horizon(days, expected):
    assert owner_pricing.duration_multiplier_basis_points(days) == expected


def test_daily_curve_is_monotone_with_small_growth_after_six_months():
    factors=[owner_pricing.duration_multiplier_basis_points(d) for d in range(1,1001)]
    assert factors==sorted(factors)
    assert min(factors)==10000 and max(factors)==12000
    growth=lambda start,end:factors[end-1]-factors[start-1]
    assert growth(180,210)<growth(30,60)
    assert growth(270,300)<growth(180,210)
    assert growth(365,1000)==0
    assert factors[180-1] / 10000 == 1.1663


@pytest.mark.parametrize('days', [0,-1])
def test_formula_rejects_missing_service_time(days):
    with pytest.raises(ValueError): owner_pricing.duration_multiplier_basis_points(days)


def test_retired_duration_permission_cannot_be_reenabled_and_presets_are_retained(tree):
    db,owner,_,_,_=tree
    policy=owner_pricing.get_policy(db)
    policy.allow_unlimited_duration=True
    db.add(OwnerDurationPreset(duration_days=60,multiplier_basis_points=13000));db.commit()
    response=owner_pricing.response(db)
    assert response.allow_unlimited_duration is False
    assert response.duration_max_multiplier==1.2
    assert response.duration_examples[-1].multiplier==1.2
    with pytest.raises(ValidationError):
        OwnerPricingUpdate(price_per_gib_toman=1000,allow_unlimited_duration=True)
    owner_pricing.update(db,owner,OwnerPricingUpdate(price_per_gib_toman=2000))
    assert db.get(OwnerDurationPreset,60).multiplier_basis_points==13000
    assert not db.get(OwnerCommercialPolicy,1).allow_unlimited_duration


@pytest.mark.parametrize('expire', [None,0,-1,1])
@pytest.mark.parametrize('owner', [False,True])
def test_no_new_user_without_future_expiry_even_for_owner(database,monkeypatch,expire,owner):
    db,_=database
    tag,_=_network(db,monkeypatch)
    admin,_=_admin(db,'required-expiry')
    admin.is_sudo=owner;db.commit()
    payload=_payload('noduration',tag).model_copy(update={'expire':expire})
    before=db.query(User).count()
    with pytest.raises(MarzhelpPolicyError) as error:
        crud.create_user(db,payload,admin=admin)
    assert error.value.code=='duration_required'
    assert db.query(User).count()==before


def test_onhold_user_requires_positive_duration_and_cannot_hide_active_unlimited_time():
    for duration in [None,0,-1]:
        with pytest.raises(MarzhelpPolicyError): require_duration(expire=None,status='on_hold',on_hold_duration=duration)
    require_duration(expire=None,status='on_hold',on_hold_duration=86400)
    with pytest.raises(MarzhelpPolicyError): require_duration(expire=None,status='active',on_hold_duration=86400)


def test_finite_creation_long_expiry_and_unlimited_edit_guard(database,monkeypatch):
    db,_=database
    tag,_=_network(db,monkeypatch)
    admin,_=_admin(db,'finite-expiry')
    user=crud.create_user(db,_payload('finite-customer',tag).model_copy(update={'expire':2200000000}),admin=admin)
    assert user.expire==2200000000
    with pytest.raises(MarzhelpPolicyError) as error:
        crud.update_user(db,user,UserModify(expire=0),actor=admin)
    assert error.value.code=='duration_required'
    db.rollback()
    assert user.expire==2200000000
    crud.update_user(db,user,UserModify(note='metadata stays editable'),actor=admin)
    assert user.note=='metadata stays editable'


def test_existing_unlimited_user_is_preserved_and_metadata_remains_editable(database):
    db,_=database
    user=User(username='historical-unlimited',status=UserStatus.active,expire=None)
    db.add(user);db.commit()
    crud.update_user(db,user,UserModify(note='historical record'))
    assert user.expire is None and user.note=='historical record'


def test_time_only_extension_buys_difference_and_cap_adds_no_charge(tree):
    db,_,_,_,_=tree
    gib=1024**3
    old=int((datetime.now(timezone.utc)+timedelta(days=30)).timestamp())
    cost=owner_pricing.adjustment_price(db,old_limit=50*gib,new_limit=50*gib,old_expire=old,new_expire=old+335*86400,old_duration_days=30,old_multiplier_basis_points=10000)
    assert cost==10000
    assert owner_pricing.adjustment_price(db,old_limit=50*gib,new_limit=50*gib,old_expire=old,new_expire=old+365*86400,old_duration_days=365,old_multiplier_basis_points=12000)==0
    # Buying 10 GiB more after waiting must retain the purchased 1.2x coefficient.
    assert owner_pricing.adjustment_price(db,old_limit=50*gib,new_limit=60*gib,old_expire=old,new_expire=old,old_duration_days=365,old_multiplier_basis_points=12000)==12000


def test_long_expiry_migration_is_replayable_and_preserves_current_data():
    spec=importlib.util.spec_from_file_location('long_expiry','app/db/migrations/versions/b6e2c9f4a810_long_finite_expiration.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    engine=sa.create_engine('sqlite://')
    with engine.begin() as conn:
        for table in ['users','next_plans']:
            conn.execute(sa.text(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY, expire INTEGER)'))
            conn.execute(sa.text(f'INSERT INTO {table} VALUES (1,2000000000),(2,NULL)'))
        conn.execute(sa.text('CREATE TABLE owner_commercial_policy (id INTEGER PRIMARY KEY, allow_unlimited_duration BOOLEAN)'))
        conn.execute(sa.text('INSERT INTO owner_commercial_policy VALUES (1,1)'))
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade();module.upgrade()
        for table in ['users','next_plans']:
            assert list(conn.execute(sa.text(f'SELECT expire FROM {table} ORDER BY id')).scalars())==[2000000000,None]
            assert isinstance(next(c['type'] for c in sa.inspect(conn).get_columns(table) if c['name']=='expire'),sa.BigInteger)
        assert conn.execute(sa.text('SELECT allow_unlimited_duration FROM owner_commercial_policy')).scalar()==0


def test_crud_time_extension_preserves_usage_and_does_not_charge_again_at_cap(tree):
    from app.db.models import AdminMoneyTransaction
    db, owner, child, user, settings = tree
    gib = 1024 ** 3
    settings.total_traffic = None
    settings.money_balance_toman = 100000
    settings.last_positive_charge_toman = 100000
    user.data_limit = 50 * gib
    user.used_traffic = 12345
    user.form_duration_days = 30
    user.duration_multiplier_basis_points = 10000
    old_expire = user.expire
    db.commit()
    crud.update_user(db, user, UserModify(expire=old_expire + 335 * 86400), actor=child)
    assert settings.money_balance_toman == 90000
    assert user.form_duration_days == 365
    assert user.duration_multiplier_basis_points == 12000
    assert user.used_traffic == 12345 and user.data_limit == 50 * gib
    count = db.query(AdminMoneyTransaction).count()
    crud.update_user(db, user, UserModify(expire=user.expire + 365 * 86400), actor=child)
    assert settings.money_balance_toman == 90000
    assert user.form_duration_days == 730
    assert user.duration_multiplier_basis_points == 12000
    assert user.used_traffic == 12345 and user.data_limit == 50 * gib
    assert db.query(AdminMoneyTransaction).count() == count
