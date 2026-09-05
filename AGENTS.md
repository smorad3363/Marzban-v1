# V1 Execution Rules

- Canonical repository: `smorad3363/Marzban-v1`; branch: `main`.
- Immutable imported baseline: tag `baseline-v1-source`, commit `0c714b182bcfd52d8eb24f1b06aa4f3f14784cf1`.
- Preserve the mature imported implementation. Make targeted, delta-only changes.
- Treat `docs/legacy-v0/` as historical reference, never active instructions.
- Active execution files: this file, `docs/CODEX/STATE.md`, and `docs/CODEX/V1_SCOPE.md`.
- On resume, read only active execution files, `git status`, recent `git log`, and any current diff; continue from `NEXT EXACT TASK`.
- Never discard valid uncommitted work automatically.
- After each coherent checkpoint: run focused tests, update `docs/CODEX/STATE.md`, and commit.
- Plan owns commercial entitlement only. Access Group owns Nodes, Inbounds, and Hosts.
- Missing required Access Group must fail closed; never grant broad or legacy Plan network access as fallback.
- Preserve existing Access Group implementation and historical migrations. Add forward migrations only when required.
- Preserve installer/release integrity safeguards. Never force-push, move immutable tags, overwrite artifacts, publish secrets, or remove `baseline-v1-source`.
- Before publication, complete required verification and compare the full diff with `baseline-v1-source`.
