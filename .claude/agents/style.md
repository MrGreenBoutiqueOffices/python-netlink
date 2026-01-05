# Code Style and API Conventions

These notes reinforce consistency across modules and error handling.

## Python Style
- Keep async/await flows clear and linear.
- Use type hints everywhere.
- Prefer dataclasses for payloads.

## API Conventions
- Preserve public API names and signatures.
- `transport="auto"` by default.
- WebSocket first, REST fallback.
- Normalize payloads before parsing.

## Docs and Examples
- Update `examples/` for user-facing changes.
- Keep public docstrings concise and clear.

## Error Handling
- 401s -> `NetlinkAuthenticationError`
- Timeouts -> `NetlinkTimeoutError`
- Command ack errors -> `NetlinkCommandError`
