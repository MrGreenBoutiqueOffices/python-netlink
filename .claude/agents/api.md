# API Surface

This summary mirrors the exported surface area; update it when public methods
or endpoints change.

## Public Exports
- Client: `NetlinkClient`
- Models: `Desk`, `DeskState`, `DeviceInfo`, `Display`, `DisplayState`
- Events: `EVENT_DESK_STATE`, `EVENT_DISPLAY_STATE`, `EVENT_DISPLAYS_LIST`,
  `EVENT_BROWSER_STATE`, `EVENT_DEVICE_INFO`, `EVENT_SYSTEM_MQTT`

## Client Methods (Selected)
- Core: `connect()`, `disconnect()`, `on(event)`
- Desk: `get_desk_status()`, `set_desk_height()`, `stop_desk()`, `reset_desk()`,
  `calibrate_desk()`, `set_desk_beep()`
- Display: `get_displays()`, `get_display_status()`, `set_display_power()`,
  `set_display_brightness()`, `set_display_volume()`, `set_display_source()`
- Browser: `get_browser_url()`, `set_browser_url()`, `refresh_browser()`
- Discovery: `discover_devices(timeout=5.0)`

## Value Ranges
- Desk height: 62.0 to 127.0 cm
- Display brightness: 0 to 100
- Display volume: 0 to 100
- Desk beep: "on" or "off" (bool allowed)

## WebSocket Command Types
- Desk: `command.desk.height`, `command.desk.stop`, `command.desk.reset`,
  `command.desk.calibrate`, `command.desk.beep`
- Display: `command.display.power`, `command.display.brightness`,
  `command.display.volume`, `command.display.source`
- Browser: `command.browser.url`, `command.browser.refresh`

## REST Endpoints
- Base URL: `http://{host}/api/v1/`
- Device: `device/info`
- Desk: `desk/status`, `desk/height`, `desk/stop`, `desk/reset`, `desk/calibrate`,
  `desk/beep`
- Displays: `displays`, `display/{bus}/status`, `display/{bus}/power`,
  `display/{bus}/brightness`, `display/{bus}/volume`, `display/{bus}/source`,
  `display/{bus}`
- Browser: `browser/url`, `browser/status`, `browser/refresh`
