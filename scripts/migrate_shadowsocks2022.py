"""One-time safe conversion of an existing Marzban Shadowsocks inbound to SS2022.

Run this with the new code and its persisted xray config already in place,
but before restarting the old running application. Use --dry-run first.
This never touches time, wallet, user status, plan pricing, or traffic counters.
"""
import argparse
import json
from pathlib import Path

from sqlalchemy import text

from app.db import GetDB
from app.db.models import Proxy, DeviceSlot, ProxyInbound, ProxyHost
from app.models.proxy import ProxyTypes
from app.utils.core_inbound_sync import synchronize_inbounds
from app.utils.shadowsocks2022 import METHOD, generate_key, valid_key


def run(config_file, old_tag, new_tag, apply):
    config = json.loads(Path(config_file).read_text())
    inbounds = {i["tag"]: i for i in config.get("inbounds", [])}
    if old_tag in inbounds:
        raise ValueError("Old Shadowsocks inbound is still in config")
    inbound = inbounds.get(new_tag)
    if not inbound or inbound.get("protocol") != "shadowsocks":
        raise ValueError("New SS2022 inbound is missing from config")
    settings = inbound.get("settings", {})
    if settings.get("method") != METHOD or not valid_key(settings.get("password")):
        raise ValueError("New SS2022 server key/method is invalid")

    proposed = {name: {"protocol": i["protocol"]} for name, i in inbounds.items()
                if i.get("protocol") in ("vmess", "vless", "trojan", "shadowsocks")}
    previous = {name: value for name, value in proposed.items() if name != new_tag}
    previous[old_tag] = {"protocol": "shadowsocks"}

    with GetDB() as db:
        old = db.query(ProxyInbound.id).filter(ProxyInbound.tag == old_tag).first()
        new = db.query(ProxyInbound.id).filter(ProxyInbound.tag == new_tag).first()
        old_host_count = db.query(ProxyHost.id).filter(ProxyHost.inbound_tag == old_tag).count()
        proxies = db.query(Proxy).filter(Proxy.type == ProxyTypes.Shadowsocks).all()
        slots = db.query(DeviceSlot).all()
        rotate = sum(
            p.settings.get("method") != METHOD or not valid_key(p.settings.get("password"))
            for p in proxies
        )
        slot_rotate = sum(
            "shadowsocks" in (s.credentials or {})
            and ((s.credentials["shadowsocks"].get("method") != METHOD)
                 or not valid_key(s.credentials["shadowsocks"].get("password")))
            for s in slots
        )
        print(f"PRECHECK: old_identity={bool(old)} new_identity={bool(new)} old_hosts={old_host_count} proxies_rotate={rotate} slots_rotate={slot_rotate}",flush=True)
        if old and new:
            raise ValueError("Old and new inbound identities both exist; manual review required")
        if not old and not new:
            raise ValueError("Neither old nor new inbound identity exists")
        if not apply:
            print("DRY RUN: no changes applied",flush=True)
            return
        if old:
            result = synchronize_inbounds(
                db, previous, proposed, rename=(old_tag, new_tag))
            print("NETWORK_RENAME:", result,flush=True)
        else:
            if db.query(ProxyHost.id).filter(ProxyHost.inbound_tag == new_tag).count() == 0:
                raise ValueError("New inbound has no hosts; refusing to proceed")
        base_credentials = {}
        rotated = 0
        for proxy in proxies:
            new_settings = dict(proxy.settings or {})
            if (new_settings.get("method") != METHOD
                    or not valid_key(new_settings.get("password"))):
                new_settings["method"] = METHOD
                new_settings["password"] = generate_key()
                proxy.settings = new_settings
                rotated += 1
            base_credentials[proxy.user_id] = dict(new_settings)
        slot_rotated = 0
        for slot in slots:
            data = dict(slot.credentials or {})
            if "shadowsocks" not in data:
                continue
            ss = dict(data["shadowsocks"])
            if slot.slot_index == 1 and slot.user_id in base_credentials:
                ss = dict(base_credentials[slot.user_id])
            elif ss.get("method") != METHOD or not valid_key(ss.get("password")):
                ss["method"] = METHOD
                ss["password"] = generate_key()
            if ss != data["shadowsocks"]:
                data["shadowsocks"] = ss
                slot.credentials = data
                slot_rotated += 1

        # Historical plan-version references are intentionally preserved on a
        # rename, unlike a removal. The main synchronizer owns active grants.
        for table in ("admin_user_plan_inbounds", "admin_user_plan_hosts"):
            db.execute(
                text(f"UPDATE {table} SET inbound_tag=:new WHERE inbound_tag=:old"),
                {"new": new_tag, "old": old_tag},
            )
        db.commit()
        print(f"APPLIED: users_rotated={rotated} slots_rotated={slot_rotated} old_tag={old_tag!r} new_tag={new_tag!r}",flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config",default="/var/lib/marzban/xray_config.json")
    p.add_argument("--old-tag",default="Shadowsocks TCP")
    p.add_argument("--new-tag",default="SHADOWSOCKS + TCP")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply",action="store_true")
    g.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    run(a.config, a.old_tag,a.new_tag,a.apply)
