# v1.1.11

Safety corrections for scheduled renewals, remaining traffic, paid Plan enforcement,
Access Group Inbound/Node/Host scope and existing Xray API listeners.
User traffic now uses non-resetting counters and transactional database cursors.
Node user history commits atomically with user usage and billing. Wall-clock
adjustments do not recharge cumulative counters. Restricted raw creation denies
seat accounts. Dashboard: ordinary Admin edits preserve separately managed Plan prices.
All backend regressions are enabled, including the three previously deselected cases.

## Installation

Use the permanent `scripts/install.sh` entry point on a fresh host. It resolves the
latest published stable release; image, configuration and CLI use one exact tag.
Existing installations use `marzban update` after backup.

## Qualification limits

Real commercial lifecycle, traffic/load and independent Panel/Node fault-injection
qualification remain pending. Cumulative Xray counters are volatile: traffic since
the last successful sample cannot be recovered if Xray resets during a database
outage. Uptime/counter regression detects observable resets; no unique persistent
Xray process identity is available for every restart. Do not describe this as
lossless accounting. Restore and restart acceptance must be checked on a test host.
