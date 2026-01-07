<!-- Banner -->
![alt Banner of the Netlink package](https://raw.githubusercontent.com/MrGreenBoutiqueOffices/python-netlink/main/assets/header_pynetlink-min.png)

<!-- PROJECT SHIELDS -->
[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE)

[![GitHub Activity][commits-shield]][commits-url]
[![PyPi Downloads][downloads-shield]][downloads-url]
[![GitHub Last Commit][last-commit-shield]][commits-url]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

[![Build Status][build-shield]][build-url]
[![Typing Status][typing-shield]][typing-url]
[![Code Coverage][codecov-shield]][codecov-url]
[![OpenSSF Scorecard][scorecard-shield]][scorecard-url]

Asynchronous Python client for Netlink desk and display control.

## About

Netlink is the operating software for smart standing desks, developed by [NetOS](https://net-os.com/). The system powers smart desks in commercial office environments, most notably at [Mr.Green Offices](https://mrgreenoffices.nl/) locations throughout the Netherlands.

This Python package provides a modern, fully typed client for controlling Netlink-equipped desks. It offers both WebSocket (for real-time state updates and fast commands) and REST API support, making it ideal for integration with Home Assistant and other automation systems.

**Target Audience:** This package is primarily intended for organizations and developers working with Netlink-equipped office environments. While publicly available on PyPI, the Netlink system itself is designed for commercial office spaces.

## Key Features

- 🔌 **Real-time state updates** via WebSocket (desk position, display settings)
- ⚡ **Fast WebSocket commands** with acknowledgements (~50% faster than REST)
- 🔄 **Smart transport** - automatic fallback from WebSocket to REST when needed
- 🔍 **mDNS/Zeroconf discovery** - automatically find Netlink devices on your network
- 📦 **Type-safe** with full type hints and mashumaro data models
- 🏠 **Home Assistant ready** with auto-reconnection and exponential backoff
- ⚡ **Async-first** using modern Python async/await patterns
- 🧪 **Production-ready** with 100% test coverage

## Installation

```bash
pip install pynetlink
```

## Quick Start

```python
import asyncio
from pynetlink import NetlinkClient

async def main() -> None:
    """Quick start example."""
    async with NetlinkClient("192.168.1.100", "your-token") as client:
        # Connect via WebSocket for real-time updates
        await client.connect()

        # Get current desk state
        if client.desk_state:
            print(f"Desk height: {client.desk_state.height}cm")

        # Control desk (automatically uses WebSocket when connected)
        await client.set_desk_height(120.0)

        # Control displays
        await client.set_display_brightness(bus_id=0, brightness=80)

        # Optional: Force specific transport if needed
        await client.set_desk_height(110.0, transport="rest")

if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation

📚 **[Complete Examples & Documentation](./examples/README.md)**

The examples folder contains comprehensive guides for:
- Device discovery with mDNS
- Real-time WebSocket events
- Desk control (height, calibration, presets)
- Display control (power, brightness, volume, input source)
- Browser control
- Error handling
- Advanced usage patterns

## Usage Examples

### Discover Devices

```python
from pynetlink import NetlinkClient

# Auto-discover devices on network
devices = await NetlinkClient.discover_devices(discovery_timeout=5.0)
for device in devices:
    print(f"Found: {device.device_name} at {device.host}")
```

### Real-time Events

```python
async with NetlinkClient(host, token) as client:
    await client.connect()

    @client.on("desk.state")
    async def on_desk_state(data: dict) -> None:
        print(f"Desk: {data['height']}cm")

    await asyncio.sleep(60)  # Listen for events
```

### Control Desk & Displays

```python
# Desk control
await client.set_desk_height(120.0)
await client.stop_desk()
await client.calibrate_desk()

# Display control
displays = await client.get_displays()
await client.set_display_power(bus_id=0, state="on")
await client.set_display_brightness(bus_id=0, brightness=80)
await client.set_display_source(bus_id=0, source="HDMI1")
```

More examples:
- [`basic_usage.py`](./examples/basic_usage.py) - Comprehensive usage with REST and WebSocket
- [`discover_devices.py`](./examples/discover_devices.py) - Device discovery with mDNS
- [`desk_state_listener.py`](./examples/desk_state_listener.py) - Real-time desk state monitoring

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Setting up development environment

The simplest way to begin is by utilizing the [Dev Container][devcontainer]
feature of Visual Studio Code or by opening a CodeSpace directly on GitHub.
By clicking the button below you immediately start a Dev Container in Visual Studio Code.

[![Open in Dev Containers][devcontainer-shield]][devcontainer]

This Python project relies on [Poetry][poetry] as its dependency manager,
providing comprehensive management and control over project dependencies.

You need at least:

- Python 3.12+
- [Poetry][poetry-install]

### Installation

Install all packages, including all development requirements:

```bash
poetry install
```

_Poetry creates by default an virtual environment where it installs all
necessary pip packages_.

### Prek

This repository uses the [prek][prek] framework, all changes
are linted and tested with each commit. To setup the prek check, run:

```bash
poetry run prek install
```

And to run all checks and tests manually, use the following command:

```bash
poetry run prek run --all-files
```

### Testing

It uses [pytest](https://docs.pytest.org/en/stable/) as the test framework. To run the tests:

```bash
poetry run pytest
```

To update the [syrupy](https://github.com/tophat/syrupy) snapshot tests:

```bash
poetry run pytest --snapshot-update
```

## License

This project is licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later). See the [LICENSE](LICENSE) file for details.

<!-- MARKDOWN LINKS & IMAGES -->
[build-shield]: https://github.com/MrGreenBoutiqueOffices/python-netlink/actions/workflows/tests.yaml/badge.svg
[build-url]: https://github.com/MrGreenBoutiqueOffices/python-netlink/actions/workflows/tests.yaml
[codecov-shield]: https://codecov.io/gh/MrGreenBoutiqueOffices/python-netlink/branch/main/graph/badge.svg?token=TOKEN
[codecov-url]: https://codecov.io/gh/MrGreenBoutiqueOffices/python-netlink
[commits-shield]: https://img.shields.io/github/commit-activity/y/MrGreenBoutiqueOffices/python-netlink.svg
[commits-url]: https://github.com/MrGreenBoutiqueOffices/python-netlink/commits/main
[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/MrGreenBoutiqueOffices/python-netlink
[downloads-shield]: https://img.shields.io/pypi/dm/pynetlink
[downloads-url]: https://pypistats.org/packages/pynetlink
[last-commit-shield]: https://img.shields.io/github/last-commit/MrGreenBoutiqueOffices/python-netlink.svg
[license-shield]: https://img.shields.io/github/license/MrGreenBoutiqueOffices/python-netlink.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[pypi]: https://pypi.org/project/pynetlink/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/pynetlink
[releases-shield]: https://img.shields.io/github/release/MrGreenBoutiqueOffices/python-netlink.svg
[releases]: https://github.com/MrGreenBoutiqueOffices/python-netlink/releases
[scorecard-shield]: https://api.scorecard.dev/projects/github.com/MrGreenBoutiqueOffices/python-netlink/badge
[scorecard-url]: https://scorecard.dev/viewer/?uri=github.com/MrGreenBoutiqueOffices/python-netlink
[typing-shield]: https://github.com/MrGreenBoutiqueOffices/python-netlink/actions/workflows/typing.yaml/badge.svg
[typing-url]: https://github.com/MrGreenBoutiqueOffices/python-netlink/actions/workflows/typing.yaml

[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[prek]: https://github.com/j178/prek
