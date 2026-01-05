# Copilot Instructions

Keep suggestions minimal and aligned with existing patterns; avoid speculative
changes outside the described scope.

## Key Paths
- Source: `src/pynetlink`
- Tests: `tests`
- Examples: `examples/`

## Environment
- Python: 3.12+
- Poetry install: `poetry install`

## Commands
- Tests: `poetry run pytest`
- Snapshot update: `poetry run pytest --snapshot-update`
- All checks (prek): `poetry run prek run --all-files`

## Guidelines
- Preserve public API behavior.
- Prefer async/await and typed models.
- Follow existing module patterns.
- Avoid committing secrets.

## Architecture Notes
- Facade: `NetlinkClient` in `src/pynetlink/netlink.py`.
- Transports: WebSocket in `src/pynetlink/websocket.py`, REST in `src/pynetlink/rest.py`.
- Events: `desk.state`, `display.state`, `displays.list`, `device.info`, `browser.state`.
