import base64
import json
import unittest
from pathlib import Path

from app.utils.shadowsocks2022 import (
    METHOD, generate_key, valid_key, client_settings, subscription_settings
)
from xray_api.proto.proxy.shadowsocks_2022.account_pb2 import Account


class TestSS2022(unittest.TestCase):
    def test_32_byte_key(self):
        for _ in range(8):
            key = generate_key()
            self.assertEqual(len(base64.b64decode(key)), 32)
            self.assertTrue(valid_key(key))
        self.assertFalse(valid_key("plain-password"))

    def test_account_type_matches_xray(self):
        self.assertEqual(Account.DESCRIPTOR.full_name, "xray.proxy.shadowsocks_2022.Account")
        self.assertEqual([f.name for f in Account.DESCRIPTOR.fields], ["key"])

    def test_core_user_has_no_method(self):
        user = {"password": generate_key(), "method": METHOD}
        payload = client_settings(user, METHOD)
        self.assertNotIn("method", payload)
        self.assertTrue(valid_key(payload["password"]))

    def test_subscription_server_user_concat(self):
        server, user = generate_key(), generate_key()
        config = subscription_settings({"password": user, "method": METHOD}, METHOD, server)
        self.assertEqual(config["password"], server + ":" + user)
        self.assertEqual(config["method"], METHOD)

    def test_invalid_manual_user_key_rejected(self):
        from pydantic import ValidationError
        from app.models.proxy import ShadowsocksSettings
        with self.assertRaises(ValidationError):
            ShadowsocksSettings(password="invalid", method=METHOD)
        self.assertTrue(valid_key(ShadowsocksSettings().password))

    def test_account_dynamic_protobuf(self):
        from xray_api.types.account import Shadowsocks2022Account
        account = Shadowsocks2022Account(email="test@local", password=generate_key())
        self.assertEqual(account.message.type, "xray.proxy.shadowsocks_2022.Account")
        self.assertTrue(account.message.value)

    def test_subscription_ss_uri_round_trip(self):
        from app.subscription.v2ray import V2rayShareLink
        server, user = generate_key(), generate_key()
        raw = subscription_settings({"password":user,"method":METHOD},METHOD,server)
        link = V2rayShareLink.shadowsocks("New profile", "203.0.113.1", 2020,
                                         raw["password"], raw["method"])
        encoded = link.split("ss://",1)[1].split("@",1)[0]
        decoded = base64.urlsafe_b64decode(encoded + "="*(-len(encoded)%4)).decode()
        self.assertEqual(decoded, METHOD+":"+server+":"+user)

    def test_dual_method_keeps_legacy_secret_and_derives_2022(self):
        from app.utils.shadowsocks2022 import user_key_2022
        classic = {"password":"original-legacy-password", "method":"chacha20-ietf-poly1305"}
        self.assertEqual(client_settings(classic, "chacha20-ietf-poly1305")["password"],
                         "original-legacy-password")
        self.assertEqual(client_settings(classic, "aes-256-gcm")["method"],
                         "chacha20-ietf-poly1305")
        modern = client_settings(classic, METHOD)
        self.assertNotIn("method",modern)
        self.assertTrue(valid_key(modern["password"]))
        self.assertEqual(modern["password"],user_key_2022(classic))
        self.assertEqual(modern["password"],client_settings(classic,METHOD)["password"])
        self.assertEqual(subscription_settings(classic,METHOD,generate_key())["method"], METHOD)

    def test_user_key_2022_unmodified_if_previously_valid(self):
        from app.utils.shadowsocks2022 import user_key_2022
        key = generate_key()
        self.assertEqual(user_key_2022({"password":key,"method":METHOD}),key)

    def test_raw_node_client_healed_from_method(self):
        from app.utils.shadowsocks2022 import normalize_inbound_clients
        raw = {"protocol":"shadowsocks", "settings":{"method":METHOD,
               "clients":[{"email":"user@local","method":METHOD,
                            "password":"old-legacy-password"}]}}
        normalize_inbound_clients(raw)
        user = raw["settings"]["clients"][0]
        self.assertNotIn("method",user)
        self.assertTrue(valid_key(user["password"]))
        classic = {"protocol":"shadowsocks", "settings":{"method":"aes-256-gcm",
                   "clients":[{"email":"old@local","method":METHOD,
                               "password":generate_key()}]}}
        normalize_inbound_clients(classic)
        self.assertEqual(classic["settings"]["clients"][0]["method"],"aes-256-gcm")

    def test_default_inbound(self):
        cfg = json.loads((Path(__file__).resolve().parents[1]/"xray_config.json").read_text())
        self.assertEqual(len(cfg["inbounds"]), 2)
        inbound = cfg["inbounds"][0]
        classic = cfg["inbounds"][1]
        self.assertEqual((classic["tag"], classic["port"]), ("Shadowsocks TCP", 1080))
        self.assertEqual(classic["settings"]["method"], "chacha20-ietf-poly1305")
        self.assertEqual((inbound["tag"],inbound["port"]), ("SHADOWSOCKS + TCP",2020))
        self.assertEqual(inbound["settings"]["method"], METHOD)
        self.assertEqual(inbound["settings"]["password"], "__AUTO_SS2022_SERVER_KEY__")


if __name__ == "__main__":
    unittest.main()
