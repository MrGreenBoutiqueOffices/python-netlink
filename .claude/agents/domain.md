# Domain Notes: Tokens, Devices, Pitfalls

Use this to capture real-world behavior and operational lessons that are not
obvious from the API surface alone.

## Token And Auth Flow
- Bearer token required for all API calls.
- REST uses `Authorization: Bearer <token>`.
- WebSocket auth uses token at Socket.IO connect.
- Local setup uses `examples/.env`.

## Known Value Ranges
- Desk height: 62 to 127 cm.
- Display brightness: 0 to 100.
- Display volume: 0 to 100.
- Bus IDs stored as strings in cache keys.

## Payload Shape Quirks
- Payloads may be wrapped as `{ "data": { ... } }`.
- Desk events may include `{ capabilities, inventory, state }`.
- Handlers normalize payloads before model parsing.

## Production Pitfalls
- WebSocket auto-reconnect uses exponential backoff.
- Use `transport="auto"` for REST fallback.
- Always call `NetlinkClient.disconnect()` to close sessions.
- Surface `NetlinkTimeoutError` to callers.
- Keep tokens out of logs, snapshots, fixtures.

## Discovery
- mDNS service: `_netlink._tcp.local.`
- Discovery returns `NetlinkDevice` with host and display info.
- Prefer stable host identifiers in production.
