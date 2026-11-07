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

    def test_default_inbound(self):
        cfg = json.loads((Path(__file__).resolve().parents[1]/"xray_config.json").read_text())
        inbound = cfg["inbounds"][0]
        self.assertEqual((inbound["tag"],inbound["port"]), ("SHADOWSOCKS + TCP",2020))
        self.assertEqual(inbound["settings"]["method"], METHOD)
        self.assertEqual(inbound["settings"]["password"], "__AUTO_SS2022_SERVER_KEY__")


if __name__ == "__main__":
    unittest.main()
