from collections import defaultdict
from types import SimpleNamespace
import asyncio
from fastapi import BackgroundTasks
from starlette.requests import Request
from app import xray
from app.db.models import ProxyHost, ProxyInbound
from app.models.admin import Admin as APIAdmin
from app.models.admin_hierarchy import AccessGroupInput, PlanCreate, PlanVersionInput
from app.models.proxy import ProxyTypes, ProxySettings
from app.utils import access_groups, admin_plans
from app.routers.admin_hierarchy import update_access_group
from app.subscription import share
from test_stage4_plan_network_scope import db, _configure_network, _runtime_host, _CaptureConfiguration


def test_explicit_network_edits_update_every_binding_slots_runtime_and_subscription(db, monkeypatch):
    monkeypatch.setattr("app.models.user.create_subscription_token", lambda username: "test-token")
    session, owner = db
    tag, host, unused = _configure_network(session, monkeypatch)
    group = access_groups.create(session, owner, AccessGroupInput(name='network', inbounds=[tag], hosts={tag:[host.id]}))
    plan = admin_plans.create_plan(session, owner, PlanCreate(name='commercial', version=PlanVersionInput(data_limit=1024, duration_days=30, concurrent_user_limit=2)))
    users=[]
    for index,status in enumerate(['active','on_hold','disabled','limited','expired']):
        user,_,_=admin_plans.create_user_from_plan(session, actor=owner, plan_id=plan.id, access_group_id=group.id, username=f'network-user-{index}', status='active', note=None, idempotency_key=f'network-user-{index}-key')
        user.status=status
        users.append(user)
    session.commit()
    original_credentials=dict(users[0].device_slots[1].credentials['vless'])
    newtag='TROJAN + WS'
    inbound={**xray.config.inbounds_by_tag[tag], 'tag':newtag, 'protocol':'trojan','port':8443}
    monkeypatch.setattr(xray.config,'inbounds_by_tag',{**xray.config.inbounds_by_tag,newtag:inbound})
    monkeypatch.setattr(xray.config,'inbounds_by_protocol',{**xray.config.inbounds_by_protocol,'trojan':[inbound]})
    newinbound=ProxyInbound(tag=newtag)
    session.add(newinbound);session.flush()
    newhost=ProxyHost(inbound=newinbound,remark='new',address='new.example')
    session.add(newhost);session.commit()
    assert access_groups._scope(session,group.id)[0]=={tag}
    assert admin_plans.subscription_host_scope(session,users[0])=={tag:{host.id}}
    calls=[]
    monkeypatch.setattr(xray.operations,'update_user_by_id',lambda user_id:calls.append(user_id))
    actor=APIAdmin(username=owner.username,is_sudo=True)
    request=Request({'type':'http','method':'PUT','path':'/api/access-groups/1','headers':[]})
    def edit(tags,hosts):
        bg=BackgroundTasks()
        update_access_group(group.id,AccessGroupInput(name='network',inbounds=tags,hosts=hosts),request,bg,session,actor)
        asyncio.run(bg())
    edit([tag,newtag],{tag:[host.id],newtag:[newhost.id]})
    assert set(calls)=={users[0].id,users[1].id}
    for user in users:
        session.refresh(user)
        assert set(user.inbounds)=={ProxyTypes.VLESS,ProxyTypes.Trojan}
        assert all(set(slot.credentials)=={'vless','trojan'} for slot in user.device_slots if slot.enabled)
    assert users[0].device_slots[1].credentials['vless']==original_credentials
    monkeypatch.setattr(share.xray,'hosts',{tag:[_runtime_host(host.id,'old','old.example'),_runtime_host(unused.id,'unselected','unused.example')],newtag:[_runtime_host(newhost.id,'new','new.example')]})
    def addresses(user):
        capture=_CaptureConfiguration()
        proxies={ProxyTypes(p.type):ProxySettings.from_dict(ProxyTypes(p.type),p.settings) for p in user.proxies}
        share.process_inbounds_and_tags(user.inbounds,proxies,defaultdict(lambda:''),capture,host_scope=admin_plans.subscription_host_scope(session,user))
        return {address for _,address in capture.remarks}
    assert addresses(users[0])=={'old.example','new.example'}
    runtime=[]
    monkeypatch.setattr(xray.operations,'_replace_inbound_users',lambda api,tag,emails,accounts:runtime.append((api,tag,len(accounts))))
    node_api=object()
    monkeypatch.setattr(xray,'nodes',{7:SimpleNamespace(api=node_api,connected=True,started=True)})
    xray.operations.update_user(users[0])
    assert {(tag,count) for api,tag,count in runtime if api is node_api}=={(tag,2),(newtag,2)}
    runtime.clear()
    edit([newtag],{newtag:[newhost.id]})
    for user in users:
        session.refresh(user)
        assert set(user.inbounds)=={ProxyTypes.Trojan}
        assert all(set(slot.credentials)=={'trojan'} for slot in user.device_slots if slot.enabled)
    assert addresses(users[0])=={'new.example'}
    xray.operations.update_user(users[0])
    assert {(tag,count) for api,tag,count in runtime if api is node_api}=={(tag,0),(newtag,2)}
