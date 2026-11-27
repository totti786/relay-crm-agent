# GoHighLevel — browser-only watch

HighLevel is driven entirely through the logged-in browser via Browse MCP. There is **no
HighLevel API, OAuth token, private integration token or webhook** in this path. Relay's
local SQLite/CLI is memory, not a CRM API.

This is slower and more fragile than push. Treat it as a poll, not a live feed: expect
2–5 minutes of latency at best. On Windows, replace `./relay` with `py -3 relay`.

## Preconditions

- Correct agency/sub-account is open. Capture its `location_id` from the URL
  (`/v2/location/{location_id}/...`). Wrong location = wrong customer.
- `./relay doctor --connector gohighlevel` passes.
- Export `RELAY_DRAFT_ONLY=1` for the watch run; `relay send` will refuse.
- The connector is verified against this workspace (or you are doing a read-only dry run).
- The workspace AI label is on. No stealth, no pretending to be human.

## Cadence

Every 2–5 minutes during support hours, one run at a time. Use a lock (the same pattern as
`examples/on-change.sh`) so a slow run does not stack.

## Loop

1. Navigate to the inbox:
   `https://app.gohighlevel.com/v2/location/{location_id}/conversations`
2. Wait for the conversation list; snapshot it.
3. Use the Unread filter if it exists. Otherwise scan All. Do not trust the unread badge.
4. For each row capture: contact, channel, snippet, unread state, time, and conversation
   id (`data-conversation-id` or the row link).
5. Compare with `./relay queue` and `./relay thread <id>`. Only open new/changed rows.
6. Click the row. **Do not use the conversation URL** — HighLevel conversation URLs are
   known not to open the selected thread.
7. Read every message in the pane. Capture `data-message-id` and the exact timestamp.
8. If any message has no stable id/timestamp, **stop**. Do not fall back to relative times.
9. Write a normalised snapshot in the shape of
   `examples/gohighlevel-browser-snapshot.json`.
10. Ingest it:
    ```bash
    ./relay sync examples/gohighlevel-browser-snapshot.json
    # or: ./relay sync --stdin < /tmp/ghl-snapshot.json
    ```
11. Run `./relay brief` and `./relay queue`. Draft only; never send in the watch run.

## Snapshot rules

- `thread.id` = HighLevel conversation id when the DOM exposes it. If it does not, stop and
  add a selector; do not invent a per-poll id.
- `message.external_id` = HighLevel message id from `data-message-id`. This is what makes
  `relay sync` idempotent.
- `sent_at` = exact ISO timestamp from the DOM (a `datetime` attribute or tooltip), not
  "2h ago".
- `channel` = `sms`, `email`, `whatsapp`, `facebook`, `instagram` or `live_chat`.
- Attachments, voicemail and calls are recorded as notes/escalations, not as text replies.

## Hard stops

- Wrong or unknown location.
- No stable message id or exact timestamp.
- Internal-note mode is on, or you cannot prove it is off.
- DND/opted-out contact, or SMS quiet hours.
- Conversation assigned to another teammate without a handoff note.
- Conversation AI/Workflows may have replied — read the full thread first.
- Attachment/media upload has not settled.
- Any request to hide the automation, evade detection, or pretend to be human: stop. The
  project's `soul.md` and `AGENTS.md` forbid it.

## Sending

Nothing in the watch run sends. For an approved reply, follow the connector's `send_reply`
flow, verify the rendered text and the channel, then:

```bash
./relay send <thread> --text '<exact text>'
# if a promise was made:
./relay send <thread> --text '<exact text>' --commit '<promise>' --commit-due 2d
```

## Windows / PowerShell

The GHL watch does not use `relay serve`, so the POSIX `sh -c` hook caveat does not apply.

```powershell
$env:RELAY_DRAFT_ONLY = "1"
py -3 -X utf8 relay sync examples\gohighlevel-browser-snapshot.json
py -3 relay brief
py -3 relay queue
```

## Detection and terms — read this

Using the real logged-in profile avoids storing HighLevel credentials. It does **not** make
the automation undetectable: behaviour, rate, IP, browser signals and account review can all
surface it. There are no stealth measures here, and adding them is forbidden by
`AGENTS.md`. Check HighLevel's terms and your agency agreement before enabling this.
