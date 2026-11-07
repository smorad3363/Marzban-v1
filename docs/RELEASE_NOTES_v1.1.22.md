# v1.1.22

Add Shadowsocks 2022 AES-256-GCM multi-user support to the default Marzban stack.

- Fresh installations use SHADOWSOCKS + TCP on port 2020 TCP/UDP with 2022-blake3-aes-256-gcm. The installer securely replaces a repository marker with a random persisted 32-byte server key. Server keys never enter GitHub.
- New users receive unique 32-byte base64 keys; API AddUser/RemoveUser uses the SS2022 protobuf Account. An internal bootstrap account keeps Xray in multi-user mode with an empty database.
- Subscription formats SS link, Clash/Meta, Sing-box, Outline and V2Ray JSON encode server_key:user_key. UI only offers the new cipher for new accounts.
- Existing installations preserve their Xray config. For deliberate replacement, first take backups and run scripts/migrate_shadowsocks2022.py with --dry-run, then --apply with a private validated config before restarting the updated application. Only Shadowsocks keys rotate; usage, balances, expiry and Trojan accounts are retained, and access-group and host references are migrated.
- Tests cover key validity, account protobuf, and URL encoding. An isolated Xray 26.10.31 experiment confirmed AddUser, end-to-end encrypted traffic, RemoveUser and revoked credentials.

Update command: marzban update --version v1.1.22

Existing Shadowsocks subscribers must refresh their subscription after migration; their port and credentials change. Unrelated inbounds and user accounting remain unchanged.
