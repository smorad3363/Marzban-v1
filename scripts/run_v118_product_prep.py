from pathlib import Path

release = Path('.github/workflows/build.yml')
text = release.read_text(encoding='utf-8')
new = '''      - name: Verify canonical dashboard UX contracts
        working-directory: app/dashboard
        run: |
          node scripts/test-stage1-ui-contracts.cjs
          node scripts/test-autofill-contract.cjs
'''
old = '''      - name: Verify canonical dashboard UX contract
        working-directory: app/dashboard
        run: node scripts/test-stage1-ui-contracts.cjs
'''
if new not in text:
    raise RuntimeError('Canonical Release autofill contract is not present')
release.write_text(text.replace(new, old, 1), encoding='utf-8')
exec(compile(Path('scripts/prepare_v118_release_candidate.py').read_text(encoding='utf-8'), 'scripts/prepare_v118_release_candidate.py', 'exec'))
if new not in release.read_text(encoding='utf-8'):
    raise RuntimeError('Release workflow was not restored after preparation')
