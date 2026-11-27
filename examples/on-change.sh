#!/usr/bin/env bash
# Draft-only agent run for webhook-triggered inbound.
# Wired via: ./relay serve --on-change ./examples/on-change.sh
# Relay sets RELAY_CHANGED_THREADS and RELAY_DRAFT_ONLY=1 for this run.
set -euo pipefail
cd "$(dirname "$0")/.."

# No exec: relay appends its hook-lock cleanup after this command.
THREADS="${RELAY_CHANGED_THREADS:-}"
[ -z "$THREADS" ] && exit 0

opencode run --auto --archived \
  --title "relay inbound: ${THREADS}" \
  --prompt "Inbound arrived on Relay threads: ${THREADS}.

For each thread: open the live CRM thread with Browse and snapshot it; compare with 'relay thread <id>'; record anything new with 'relay log <id> --kind note --text ...'. Then write a reply draft with 'relay draft <id> --text ...'.

Do not send and do not approve. RELAY_DRAFT_ONLY is set; 'relay send' will refuse. Finish by printing the draft ids and one line on why each reply is correct."
