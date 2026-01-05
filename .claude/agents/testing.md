# Testing Notes

Focus on tests that validate external behavior and guard against regressions.

## Commands
- Tests: `poetry run pytest`
- Snapshot update: `poetry run pytest --snapshot-update`

## Tips
- Prefer targeted tests for faster feedback.
- Snapshot tests use syrupy; review diffs.
- Mock or isolate network-dependent behavior.

## Test Layout
- `tests/test_netlink.py`: client behavior and transport selection.
- `tests/test_websocket.py`: Socket.IO events and command acks.
- `tests/test_rest.py`: REST request and error mapping.
- `tests/test_models.py`: dataclass parsing and snapshots.
- Fixtures: `tests/fixtures/`, snapshots: `tests/__snapshots__/`.
