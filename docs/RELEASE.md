# V1 Release Procedure

Latest **verified stable release**: [v1.1.10](https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.10), published 2026-10-16 from source `b09801ca922199b06eaf43938664544331328668`. The published digest and verification evidence are in [STATE](STATE.md).

For a **future** release:
1. Verify exact `main` SHA, latest stable release, unused next patch tag, branch rules, baseline comparison and clean diff (including secrets, deletions and broken links).
2. Synchronize `VERSION`, `app.__version__`, `scripts/marzban.sh`, `docker-compose.yml`, `RELEASES.md` and versioned release notes. Frontend workspace package version is independent.
3. Before merge, inspect every required PR job on the exact final head: both MySQL matrix engines, migrations/current backup, dashboard source/build parity, installer/Compose/image and Panel/Node mTLS. **SKIPPED** is not **PASS**.
4. Merge only after verified gates. Create a new immutable version tag on the exact reviewed main commit; do not move or reuse any tag. Use canonical `.github/workflows/build.yml` (tag event or official workflow dispatch) to publish GHCR version/SHA multiarch images and GitHub Release.
5. Verify tag/source, `linux/amd64` and `linux/arm64`, OCI image digest/revision, anonymous pull and runtime. Dispatch `verify-v1-image.yml` and isolated `validate-v1-installer.yml` against the exact digest; record PASS/FAIL/SKIPPED and evidence in a separate documentation commit.
6. Never deploy to live servers, alter external volumes, remove historical releases or rewrite tags as part of release verification.

## Published v1.1.10 installation commands

```bash
marzban update --version v1.1.10
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.10/scripts/marzban.sh)" @ install --version v1.1.10 --database mysql
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.10/scripts/marzban.sh)" @ install-script v1.1.10
sudo marzban node install --version v1.1.10
```
