import pytest
from app import xray
from app.db.models import ProxyHost, ProxyInbound
from app.models.admin_hierarchy import AccessGroupInput, PlanCreate, PlanVersionInput
from app.utils import access_groups, admin_plans
from test_stage4_plan_network_scope import db, _configure_network


@pytest.mark.parametrize('rename',[False,True])
def test_core_tag_delete_or_rename_fails_closed_until_explicit_group_repair(db,monkeypatch,rename):
    session,owner=db
    old,host,_=_configure_network(session,monkeypatch)
    retained='UNCHANGED VLESS'
    safe_config={**xray.config.inbounds_by_tag[old],'tag':retained,'port':8443}
    configs={**xray.config.inbounds_by_tag,retained:safe_config}
    monkeypatch.setattr(xray.config,'inbounds_by_tag',configs)
    monkeypatch.setattr(xray.config,'inbounds_by_protocol',{'vless':list(configs.values())})
    inbound=ProxyInbound(tag=retained);session.add(inbound);session.flush()
    safe_host=ProxyHost(inbound=inbound,remark='safe',address='safe.example')
    session.add(safe_host);session.commit()
    group=access_groups.create(session,owner,AccessGroupInput(name='core-tag-group',inbounds=[old,retained],hosts={old:[host.id],retained:[safe_host.id]}))
    plan=admin_plans.create_plan(session,owner,PlanCreate(name='commercial-core-tag',version=PlanVersionInput(data_limit=1024,duration_days=30)))
    user,_,_=admin_plans.create_user_from_plan(session,actor=owner,plan_id=plan.id,access_group_id=group.id,username='core-tag-user',status='active',note=None,idempotency_key='core-tag-create')
    credentials=[(proxy.type,dict(proxy.settings)) for proxy in user.proxies]
    next_configs={retained:safe_config}
    if rename: next_configs['RENAMED VLESS']={**configs[old],'tag':'RENAMED VLESS'}
    monkeypatch.setattr(xray.config,'inbounds_by_tag',next_configs)
    monkeypatch.setattr(xray.config,'inbounds_by_protocol',{'vless':list(next_configs.values())})
    assert access_groups._scope(session,group.id)[0]=={old,retained}
    assert access_groups.user_inbound_scope(user)==set()
    assert admin_plans.subscription_host_scope(session,user)=={}
    access_groups.update(session,owner,group,AccessGroupInput(name=group.name,inbounds=[retained],hosts={retained:[safe_host.id]}))
    assert access_groups.user_inbound_scope(user)=={retained}
    assert admin_plans.subscription_host_scope(session,user)=={retained:{safe_host.id}}
    assert [(proxy.type,dict(proxy.settings)) for proxy in user.proxies]==credentials
