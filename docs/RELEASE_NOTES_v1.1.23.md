# v1.1.23

Fix Shadowsocks 2022 multi-user node 503 errors while supporting classic Shadowsocks simultaneously.

- Node and master Xray startup configurations strip method from every Shadowsocks 2022 client and keep valid per-user legacy methods only for classic Shadowsocks.
- Use the same user, quota and traffic accounting across both inbounds. A valid existing 32-byte 2022 key stays unchanged; a legacy password produces a stable, domain-separated 32-byte 2022 key without changing the legacy password or database.
- Dynamic AddUser/RemoveUser and account replacement apply the same method and key mapping as initial boot. Access Group scopes and Node filters remain intact.
- Fresh installs include a legacy Shadowsocks TCP inbound on 1080 and SS2022 on 2020; SS2022 server key remains private and installer-generated. Existing local configurations are deliberately preserved, including ports and hosts.
- The dashboard allows choosing modern and classic methods. Node configuration and real core tests enforce independent user ciphers.
- Does not alter plan pricing, accounting, permissions, traffic, Trojan or other protocols.

Update: marzban update --version v1.1.23
