# AGENTS

Use this as a quick operational map of the repo for agents; keep it concise and
prioritize details that help with navigation, safe changes, and testing.

## Quick Context
- Package name: `pynetlink`
- Source: `src/pynetlink`
- Tests: `tests`
- Examples: `examples`
- Docs/examples: `examples/README.md`
- Public entrypoint: `NetlinkClient` in `src/pynetlink/netlink.py`

## Environment
- Python: 3.12+
- Dependency manager: Poetry

## Common Commands
- Install deps: `poetry install`
- Run tests: `poetry run pytest`
- Update snapshots: `poetry run pytest --snapshot-update`
- Lint/test all (prek): `poetry run prek run --all-files`

## Development Notes
- Prefer async/await patterns and typed models.
- Keep changes compatible with the existing public API.
- Use WebSocket first, REST as fallback when relevant.
- Avoid committing secrets; sample env lives in `examples/.env`.

## Architecture At A Glance
- `src/pynetlink/netlink.py`: facade that combines WebSocket events + REST commands.
- `src/pynetlink/websocket.py`: Socket.IO client, event callbacks, command acks.
- `src/pynetlink/rest.py`: REST transport, request timeout, auth headers.
- `src/pynetlink/models/`: typed dataclasses for desk, display, device, browser.
- `src/pynetlink/const.py`: event names, timeouts, discovery constants.
- `src/pynetlink/exceptions.py`: Netlink* errors used across transports.

## Events And Transports
- WebSocket events: `desk.state`, `display.state`, `displays.list`, `device.info`,
  `browser.state`, `system.mqtt`.
- `transport="auto"` uses WebSocket if connected, else REST.
- WebSocket commands use `command.*` types and expect `command_ack`.

## REST Endpoints (Examples)
- Device info: `GET /api/v1/device/info`
- Desk: `POST /api/v1/desk/height`, `POST /api/v1/desk/stop`, `POST /api/v1/desk/reset`
- Displays: `GET /api/v1/displays`, `GET /api/v1/display/{bus}/status`
- Browser: `GET /api/v1/browser/url`, `POST /api/v1/browser/refresh`

## Testing Notes
- Tests live in `tests/`, fixtures in `tests/fixtures/`.
- Snapshots: `tests/__snapshots__/test_models.ambr`.
- Use targeted tests when possible to keep cycles fast.

## AI Assist Notes
- Claude: `CLAUDE.md` (repo root) and `.claude/agents/`.
- Copilot: `.github/copilot-instructions.md`.

## Release/Quality
- CI uses pytest and typing checks; keep coverage high.
- Follow existing code style and patterns in `src/pynetlink`.
