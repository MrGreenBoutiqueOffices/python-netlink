# Claude Instructions

These notes are optimized for fast onboarding and safe edits; prefer the linked
agent docs for deeper guidance.

## Repo Overview
- Core package: `src/pynetlink`
- Public entrypoint: `NetlinkClient`
- Tests: `tests`
- Examples/docs: `examples/` and `examples/README.md`

## Setup
- Python: 3.12+
- Install deps: `poetry install`

## Common Commands
- Tests: `poetry run pytest`
- Snapshot update: `poetry run pytest --snapshot-update`
- All checks (prek): `poetry run prek run --all-files`

## Coding Guidelines
- Preserve public API names and signatures.
- Prefer async/await and typed models.
- Follow existing module structure and style.
- Do not add secrets; use `examples/.env`.

## Project Notes
- WebSocket preferred; REST fallback.
- Keep compatibility with Home Assistant and automation use cases.

## Public API Highlights
- Client: `NetlinkClient(host, token, request_timeout=5.0, session=None)`
- State cache: `client.desk_state`, `client.displays`, `client.device_info`
- Events: `client.on("desk.state")`, `client.on("display.state")`, `client.on("device.info")`
- Discovery: `await NetlinkClient.discover_devices(timeout=5.0)`

## Error Types
- Base: `NetlinkError`
- Connection/auth/timeouts: `NetlinkConnectionError`, `NetlinkAuthenticationError`,
  `NetlinkTimeoutError`
- Command ack failures: `NetlinkCommandError`

## Examples And Env
- Example setup: `cp examples/.env.example examples/.env`
- Docs/examples: `examples/README.md`
- Do not commit real tokens.

## Extra Context
- See `.claude/agents/overview.md` for architecture and main modules.
- See `.claude/agents/api.md` for exported API, events, and endpoints.
- See `.claude/agents/domain.md` for token flow and production pitfalls.
- See `.claude/agents/testing.md`, `.claude/agents/style.md`,
  `.claude/agents/contributing.md` for workflow notes.
- Add reusable slash commands in `.claude/commands/`.
