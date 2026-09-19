# Product-first R07.a — recovery archive provenance and executable-workspace blocker

Date: 2026-09-19. Authority: user-supplied FINAL v3.1 ZIP, controlling Persian `ROADMAP-fa.md` R07, repository `AGENTS.md`, and preceding [R07.a blocker](product-first-r07a-environment-blocker-checkpoint.md). The user requested continued execution THROUGH ALL R07.a–d, without premature completion. This checkpoint records additional independent attempts to recover a correct executable source checkout, not an implementation. Do not interpret a documentation commit as completion of R07.

## Pinned source and unchanged execution state

```yaml
repo: smorad3363/Marzban-v1
branch: docs/product-first-v3-1-r01-ledger
verified_parent_head_before_this_checkpoint: 85d9e00d38555456cefe3f1fa4314c43ba1bd051
pinned_branch_version: 1.1.9
stage: R07
stage_state: BLOCKED_ENV_NOT_DONE
R07.a: BLOCKED_NO_CORRECT_EXECUTABLE_CHECKOUT
R07.b: NOT_STARTED
R07.c: NOT_STARTED
R07.d: NOT_STARTED
source_edits: NONE
migration_edits: NONE
runtime_tests: NOT_RUN
fresh_install_and_populated_upgrade: NOT_RUN
live_database_access: NONE
other_machine_uncommitted_state: UNKNOWN
release_gate: LOCKED_IMPLEMENTATION
main_version_release_deploy: UNCHANGED_NOT_AUTHORIZED
next_exact_action: 'Obtain a complete, matching Git checkout of the current safe branch (reverify its new HEAD including THIS checkpoint), using working GitHub network/Work computer or a trusted supplied checkout with source and Git metadata; do not copy old archives over it. Verify git rev-parse HEAD, git status --short, git diff --stat and git diff without discarding changes. Then implement/test R07.a schema/model plus additive migration first, run truly isolated fresh-install and seeded-upgrade checks, commit independently; continue R07.b owner create/edit, R07.c archive/restore/ref protections, R07.d new-product-path Plan separation only after predecessor verified. Stop at R07; do not touch R08, main, VERSION, live DB, tags, release or deploy.'
```

## Source recovery attempts and why alternatives are not safe

1. GitHub connector read exact branch HEAD `85d9e00d38555456cefe3f1fa4314c43ba1bd051`, its tree and current `VERSION` (`1.1.9`). The connector can return individual text files and create scoped commits, but does not expose a complete mounted Git checkout, shell or executable tests; GitHub `zipball/{SHA}` is not an allowed fetch URL through this connector.
2. Container preflight found no `.git` repository in accessible workspace roots. DNS lookup for `github.com` returned no address. Direct HTTPS test with explicitly resolved GitHub IP `140.82.112.3:443` also returned connection refused, so DNS-only mitigation was not enough. A pinned GitHub archive download via the available download path could not be obtained.
3. Inspected all ZIP filenames in accessible Library: the newest September 19 FINAL/Revised ZIPs are Product **specification bundles**, not source. The available full-source archive `Marzban-5.1.0.zip` contains 724 entries and `VERSION=5.1.0`; its `AGENTS.md` Git blob is `7d31f4792221a38cc479caaf368b50e38aa44cad`, `app/db/models.py` blob is `39d899d5433a2fe6f6962f225bc8bbbcd887decc`, and `VERSION` blob is `831446cbd27a6de403344b21c9fa93a25357f43d`, not the target pinned `AGENTS.md=209fe785e7ecf5d453118d457778e7eaad3d7c5d`, `models.py=0f4631074901ed7c1e2f75f1d95c0c58660fb620`, `VERSION=512a1faa68010937a4b758aa6579efd68946d40f`. It has no Git metadata.
4. Also materialized older `Marzban-ChatGPT-Web-Review-20260903.zip` and `Marzban-ChatGPT-Review-20260826.zip`, which both report `VERSION=5.0.0-rc.13`, `models.py` Git blob `f08e2e595e39a358d682f450fa0732f3b174d4f2`; these are not branch `1.1.9`. The 419-MB Library `vProject(2).rar` was inspected *read-only* through libarchive, listing 35,521 entries with only root groups `marzban` (34,751) and `Marzban-vNext` (768), and no `Marzban-v1`, `product-first-v3-1`, or `baseline-v1-source` path. Its two checked Git origins target `smorad3363/Marzban-vNext` / `smorad3363/Marzban`, and `Marzban-vNext/VERSION=5.1.0`. No old archive may be silently promoted to current source or copied over a user's actual worktree.
5. Installed pytest, SQLAlchemy and Alembic in the isolated container do **not** imply tests can execute against a missing exact source checkout. No `pytest`, `alembic`, installer, production query, migration, rollback or restart was executed. No failing/passing implementation test, CI success or database emptiness is claimed. This is a reproducible environment/provenance blocker, not a finding that Product implementation itself is impossible.

## Non-destructive unblock, acceptance and stopping rule

- Restore network-accessible Git clone of `smorad3363/Marzban-v1` on the current safe branch, or use an authorized coding workspace with an exact verified repository checkout and executable tooling, or supply an exact branch source checkout through a supported attachment route (sanitize secrets before transfer). Preserve other-machine uncommitted work and do not assume any ZIP equals branch HEAD from its filename. An archive without `.git` may be used only after strict file/tree comparison and does not establish original dirty state.
- For R07.a first: write focused failing model/schema tests, minimal Product identity and separate validated Inbound/Host mapping with Owner FK, positive multiplier default 1 and no Product quota/term/base/fixed-price fields; use an additive migration without dropping legacy Plans, groups, users, ledger or Trial. Actually run tests and disposable clean/seeded upgrades. Then independently verify R07.b/c/d and stage acceptance (Owner-only CRUD, secure archive and referenced-delete protections, Product-only new path). No claimed PASS without executed evidence.
- The previously recorded R07.a checkpoint remains authoritative for feature scope. This new checkpoint **adds only source-recovery evidence**. Verify this one-file docs commit with full readback, direct-parent compare, safe branch and unchanged main HEAD, and exact-SHA CI/status; do not mark absent checks as PASS. Release stays LOCKED.