# V1 Release Procedure

Previous verified stable tag: `v1.1.9`; proposed new maintenance tag: `v1.1.10` **only if unused and fully tested**.

1. Verify exact main SHA, latest stable Releases and absence of proposed tag. Check release candidate diff for secrets, broken links, deletions, and immutable `baseline-v1-source` comparison.
2. Synchronize `VERSION`, `app.__version__`, `scripts/marzban.sh` CLI release version, `docker-compose.yml` image, `RELEASES.md` and `docs/RELEASE_NOTES_vX.Y.Z.md`. Frontend workspace package version is independent.
3. On PR, verify every backend MySQL matrix job, current migrations/backup, UI source+build parity, installer/Compose/image, Panel/Node mTLS and required branch checks; skipped is not passed.
4. Only after verified gates merge. Tag the exact reviewed commit on `main`, never rewrite an existing tag. Official tag-triggered `.github/workflows/build.yml` publishes version and SHA GHCR images and GitHub Release; verify linux/amd64 + linux/arm64 manifests, digest, source revision, immutable tag and release notes.
5. Use manual image verifier and disposable fresh-install verifier with exact digest/tag/SHA when supported. Never deploy into live server or erase existing data. If verification is blocked, do not claim completed publication. Follow with a separate docs/STATE.md commit for observed outcomes and release/doc commit IDs.

After verified v1.1.10 publication only:
```bash
marzban update --version v1.1.10
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.10/scripts/marzban.sh)" @ install --version v1.1.10 --database mysql
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.10/scripts/marzban.sh)" @ install-script v1.1.10
sudo marzban node install --version v1.1.10
```
