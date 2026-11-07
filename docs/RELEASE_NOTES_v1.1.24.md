# v1.1.24

Reduce the risk of accumulated idle connections and GC CPU pressure on standalone Nodes using classic Shadowsocks and SS2022.

- Built-in Node Runtime V2 defaults to a balanced profile: Go memory budget is 75% of effective RAM, including a smaller container/cgroup limit, with GOGC=50 unless explicitly configured otherwise.
- Apply handshake=15s, connIdle=120s and bufferSize=64KiB to Node policy levels. Preserve stricter settings, account keys, per-user traffic flags and routing. SS2022 crypto buffers remain implementation-managed; this is not a hard RSS cap.
- Preserve a deliberately smaller GOMEMLIMIT on a shared host and retain memory settings during Node updates. XRAY_NODE_MEMORY_PROFILE=off disables automatic memory/policy tuning.
- Strip redundant per-user SS2022 methods at the Node wire boundary without deriving or replacing any key. Classic per-user ciphers remain unchanged.
- Official images use Xray v26.10.31 with pinned SHA256 archive checks for linux/amd64 and linux/arm64. Report a warning when an explicitly selected older core may ignore SS2022 policies. Existing separately installed standard Nodes require their core to be checked independently.
- Keep existing installation/update commands and strict Panel-to-Node mTLS. A standalone Node receives no panel private key and runs no database.
- Extend the disposable Node lab to verify the actual Go child environment under a 384MiB container limit, real TCP payload hashes, UDP echo, idle cleanup, and restart for both classic SS and SS2022.

Node update: `marzban node update --version v1.1.24`

Panel packages use the existing `marzban update --version v1.1.24` command.
Existing dashboard behavior, Access Group enforcement and commercial accounting are retained.

This release does not change plans, billing, permissions, account credentials, or automatically migrate standard Gozargah Nodes to the built-in runtime.
