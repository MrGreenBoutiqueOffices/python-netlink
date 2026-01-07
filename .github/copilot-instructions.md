# Copilot Instructions

Keep changes minimal and aligned with existing patterns; avoid speculative scope.
Preserve the public API (names/signatures/behavior) unless explicitly requested.

## Repo Map (where to look)
- Facade client: `NetlinkClient` in `src/pynetlink/netlink.py`
- Transports: `src/pynetlink/websocket.py` (Socket.IO) and `src/pynetlink/rest.py` (aiohttp)
- Typed models: `src/pynetlink/models/` (mashumaro `DataClassDictMixin`)
- Constants: `src/pynetlink/const.py` (event names, default timeouts, API version)
- Errors: `src/pynetlink/exceptions.py` (`Netlink*` exception hierarchy)
- Tests/fixtures: `tests/` + `tests/fixtures/*.json` + snapshots in `tests/__snapshots__/`

## Dev Workflows
- Install: `poetry install`
- Tests: `poetry run pytest` (async tests; snapshot assertions via syrupy)
- Update snapshots: `poetry run pytest --snapshot-update`
- All checks (CI-like): `poetry run prek run --all-files` (consider `poetry run prek install`)

## Project Conventions (important for correct behavior)
- Async-first: `NetlinkClient` is an async context manager; WebSocket connects via `await client.connect()`.
- Transport routing: many methods take `transport="auto"|"websocket"|"rest"`; `"auto"` means “WebSocket if connected, else REST”. Keep this semantics.
- WebSocket payload normalization:
	- Socket.IO handlers may pass multiple args; the code uses the first payload.
	- Events often arrive wrapped in `{"data": ...}`; unwrap before parsing.
	- `NetlinkClient._on_desk_state` accepts JSON strings (fixtures) and may unwrap nested `{"state": {...}}`.
- State cache is owned by `NetlinkClient` and updated from WS events:
	- `client.desk_state: DeskState | None`
	- `client.displays: dict[str, Display]` keyed by **string** bus id (`"20"`)
	- `client.device_info: DeviceInfo | None`
- WebSocket commands:
	- Commands emit `"command"` with `{type, id, data}` and await `"command_ack"`.
	- Failures/timeout map to `NetlinkConnectionError` / `NetlinkTimeoutError` / `NetlinkCommandError`.
- Models:
	- Prefer `.from_dict()` / `.to_dict()` (`mashumaro.DataClassDictMixin`).
	- `__post_init__` is used for coercion/validation (e.g., `Desk.state` dict → `DeskState`), raising `NetlinkDataError` for invalid/incomplete payloads.

## Integration Points
- HTTP API base is `http://{host}/api/v1/…` with `Authorization: Bearer <token>` (see `NetlinkREST._request`).
- Discovery uses Zeroconf/mDNS (`NetlinkClient.discover_devices`) for `_netlink._tcp.local.`; credentials still require the bearer token.
- Secrets: examples load `examples/.env`; never commit real tokens.
