from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "app/dashboard/scripts/test-admin-ux.cjs"
s = p.read_text()

old_read = 'const nodeBandwidthPanel = read("src/components/NodeBandwidthPanel.tsx");'
new_read = 'const nodesWorkspace = read("src/components/NodesManagementWorkspace.tsx");'
if old_read not in s:
    raise SystemExit("stale NodeBandwidthPanel test fixture not found")
s = s.replace(old_read, new_read, 1)

old_dashboard = 'assert.ok(dashboard.includes("{isOwner && <NodeBandwidthPanel />}"), "Owner dashboard must render the real node bandwidth panel");'
new_dashboard = 'assert.ok(!dashboard.includes("NodeBandwidthPanel"), "Dashboard must not render the removed node bandwidth panel");'
if old_dashboard not in s:
    raise SystemExit("stale Dashboard bandwidth assertion not found")
s = s.replace(old_dashboard, new_dashboard, 1)

old_endpoint = 'assert.ok(nodeBandwidthPanel.includes(\'fetch("/nodes/bandwidth")\'), "node bandwidth panel must use the real bounded node bandwidth endpoint");'
new_endpoint = 'assert.ok(nodesWorkspace.includes(\'fetch("/nodes/bandwidth")\') && nodesWorkspace.includes("nodes-live-bandwidth"), "Node Management workspace must own the real bounded live bandwidth data");'
if old_endpoint not in s:
    raise SystemExit("stale node bandwidth endpoint assertion not found")
s = s.replace(old_endpoint, new_endpoint, 1)

p.write_text(s)
