# Project Overview

This file is a quick map of the main modules and data flow; keep it aligned
with the actual code layout.

## What This Repo Is
- Async Python client for Netlink desks and displays.
- Primary entrypoint: `NetlinkClient` in `src/pynetlink/netlink.py`.
- Stable public API for desk, display, and browser control.

## Core Modules
- Facade: `src/pynetlink/netlink.py`
- WebSocket transport: `src/pynetlink/websocket.py`
- REST transport: `src/pynetlink/rest.py`
- Models: `src/pynetlink/models/`
- Constants: `src/pynetlink/const.py`
- Errors: `src/pynetlink/exceptions.py`
- Public exports: `src/pynetlink/__init__.py`

## Behavior Notes
- WebSocket preferred; REST fallback when disconnected.
- Cached state: desk, display, device info.
- Discovery uses mDNS/zeroconf via `NetlinkClient.discover_devices`.
- Commands use `command.*` with `command_ack`.

## Data Flow (High Level)
- `connect()` opens Socket.IO and registers handlers.
- Payloads are normalized before model parsing.
- `transport="auto"` chooses WebSocket when connected.
- REST uses bearer auth header.

## Where To Look First
- Public API: `src/pynetlink/netlink.py`
- Transport: `src/pynetlink/websocket.py`, `src/pynetlink/rest.py`
- Models: `src/pynetlink/models/`
