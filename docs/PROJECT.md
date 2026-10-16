# Marzban V1 — Project and owner-approved scope

As of 2026-10-16, the repository is `smorad3363/Marzban-v1` (main). This describes the current source contract, not an independently verified staging deployment.

## Product architecture

The existing application comprises a FastAPI/Python backend, MySQL/InnoDB and Alembic migrations, a React/TypeScript dashboard with committed build artifacts, Docker Compose panel, and a separately deployed built-in Node Runtime using certificate-based Panel-to-Node mTLS.

- **Plan** exclusively owns commercial terms (volume, time, price and renewal behavior).
- **Access Group** exclusively owns network scope (Nodes, Inbounds, Hosts). Missing required Access Group fails closed, never falling back to broad Plan network access.
- Owner and delegated Admin permissions and financial privacy must be enforced in the backend.
- Keep the authoritative existing traffic-usage collector, accounting ledger, immutable history of current-version operations, safe Admin retirement, device limits, retry/idempotency, bulk jobs, backup/restore and Node reconnect guarantees.

## Confirmed Owner decision: fresh install

**CONFIRMED BY OWNER:** There are no previous real operational Users, reseller Admins, or historical production databases to preserve or upgrade for the planned deployment. Initial installation uses a new **empty MySQL database**. Fixtures/synthetic test data do not imply historic production users.

**Required present-version tests:** database bootstrap to Alembic head; first Owner creation/login; new Admin hierarchy/access; credit, billing, usage and history; Plan and Access Group; User creation, renewal, deletion; backup and restore of newly created records; fresh Panel/Node installation and mTLS; service restart and reconnect; concurrency, security, idempotency and fail-closed behavior.

**Outside this milestone's requirements:** v4/vNext product-line migration, backfill of former users/roles, and rollback into old application releases. This does **not** authorize removing Alembic migrations needed for fresh installation, weakening current-version accounting/security tests, deleting runtime code by name alone, or modifying external databases, servers, volumes or published tags.

Historic Owner/Admin plans and retired handoffs are non-authoritative historical records. Future implementation work requires separate scope approval; see [ROADMAP](ROADMAP.md).
