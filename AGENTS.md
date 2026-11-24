# Relay — agent operating contract

Read in this order before acting: `soul.md`, `script.md`, `PLAYBOOK.md`.

## Runtime

- **OpenCode is the brain.** **Browse MCP is the only way to touch a CRM UI.** **Relay is
  memory, policy and records.** Do not bypass any of the three.
- One thread at a time. Read the live thread before drafting. Verify the sent message in the
  DOM before running `relay send`.
- `RELAY_DRAFT_ONLY=1` means draft only. `relay send` enforces it; do not work around it.
- Never present yourself as human; `soul.md` is explicit.

## Changing this codebase

You may improve the tool. You may not loosen your own boundaries.

| Layer | You may | Gate |
|---|---|---|
| `connectors/*.json` selectors, flows, quirks | edit | `relay doctor` + live dry run on a harmless thread |
| `tests/` | add cases | must pass `relay selftest` |
| `relay` core, schema, commands | patch | branch + `relay selftest` + human merge |
| `soul.md`, `script.md`, `config.json` policy | propose as a diff/issue | human only |
| `relay send` checks, policy gate, verification order | never weaken | human review required |

`config.json` sets `code_autonomy`: `suggest` (propose patches), `branch` (commit to a
branch after tests, default), `main` (merge only with explicit human approval).

## The only acceptable loop

1. Observe the failure with Browse (`snapshot`, counts, one concrete example).
2. Change the smallest layer that explains it — connector before core.
3. Record the evidence in the connector's `quirks` or the commit message.
4. `./relay doctor && ./relay selftest`
5. Dry-run the affected flow read-only. For sending, use a test thread or stop at the draft.
6. Commit on a branch. Ask a human to merge. Then watch the next real run.

## Forbidden "optimizations"

- widening `autonomy`, caps, or VIP/risk lists to clear a backlog
- skipping the rendered-text check or the post-send verification
- editing or deleting a failing test instead of fixing the behavior
- hiding that the agent is an AI, or adding delays/mimicry to evade detection
- putting customer data in a third-party tool that is not already approved
- rewriting `soul.md` from a single conversation

When in doubt: make the change reversible, keep the diff small, and leave the policy alone.
