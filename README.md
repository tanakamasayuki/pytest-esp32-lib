# pytest-esp32-lib

[日本語版はこちら](README.ja.md)

Minimal Arduino library and test projects for experimenting with `pytest` on ESP32 boards.

This repository contains two parts:

- A tiny Arduino library, `addTest`, with a simple `add(int, int)` API
- A `tests/` workspace built around `pytest`, `pytest-embedded`, and `arduino-cli`

The goal is not to provide a full framework. It is a small, practical reference project for:

- Building Arduino sketches from `pytest`
- Running hardware tests on ESP32 boards
- Switching Arduino CLI sketch profiles such as `esp32` and `esp32s3`
- Passing environment-specific values such as Wi-Fi credentials into test sketches

## Repository Layout

- `src/`
  Arduino library sources
- `examples/`
  Minimal example sketch for the library
- `tests/`
  Python test workspace, hardware test sketches, runner scripts, and local config

Inside `tests/`, there are three example runner sketches:

- `esp32_serial_runner`
  Verifies plain serial output without Unity
- `esp32_unity_runner`
  Runs multiple Unity tests on the device
- `esp32_wifi_runner`
  Connects to Wi-Fi and verifies that the device gets an IP address

## Requirements

- Python 3.13+
- `uv`
- `arduino-cli`
- A supported ESP32 board connected over serial

The ESP32 Arduino core does not have to be preinstalled manually if you use the provided `sketch.yaml` files.

Typical Python dependencies are managed in `tests/pyproject.toml`.

## Test Environment

The `tests/` directory is a self-contained test workspace.

It includes:

- `conftest.py`
  Shared `pytest` logic for build/test flow
- `pytest.ini`
  `pytest-embedded` and `pytest-html` defaults
- `run.*`, `run_build.*`, `run_test.*`
  Helper scripts for Linux/WSL and Windows
- `clean.*`
  Cleanup scripts for generated files

## Running Tests

### Linux / WSL

Run all build and test steps:

```bash
./tests/run.sh
```

Run build only:

```bash
./tests/run_build.sh
```

Run test only:

```bash
./tests/run_test.sh
```

Run build in WSL and then execute the Windows serial-side test runner:

```bash
./tests/run_wsl.sh
```

### Windows

Run all build and test steps:

```bat
tests\run.bat
```

Run build only:

```bat
tests\run_build.bat
```

Run test only:

```bat
tests\run_test.bat
```

## Common Options

The project supports these custom `pytest` options:

- `--run-mode=all|build|test`
- `--profile <profile-name>`

Examples:

```bash
./tests/run.sh --profile esp32s3
./tests/run_test.sh --profile esp32s3 tests/esp32_unity_runner/test_unity_runner.py
```

If `--profile` is omitted, the build uses the sketch's default profile and stores artifacts under `build/default`.

## Serial Port Selection

Serial port selection is intentionally left to `pytest-embedded` defaults.

Use either:

- `--port`
- `ESPPORT`

Examples:

```bash
ESPPORT=/dev/ttyUSB0 ./tests/run.sh
```

```bat
set ESPPORT=COM5
tests\run.bat
```

## Local Environment Variables

The test workspace supports local dotenv files:

- `tests/.env`
- `tests/.env.local`

These files are treated as defaults and do not override real environment variables already set in the shell.

An example file is provided:

- `tests/.env.example`

Typical values:

```env
TEST_WIFI_SSID=your-ssid
TEST_WIFI_PASSWORD=your-password
```

## Build-Time Defines

Some test sketches can receive values as compile-time defines.

For example, `tests/esp32_wifi_runner/build_config.toml` maps environment variable names to Arduino defines:

```toml
[defines]
TEST_WIFI_SSID = "TEST_WIFI_SSID"
TEST_WIFI_PASSWORD = "TEST_WIFI_PASSWORD"
```

In this mapping:

- the left-hand side is the environment variable name to read
- the right-hand side is the `#define` name passed to the sketch build

During build, `conftest.py` resolves the current environment values and passes them to `arduino-cli` using `--build-property`.

## Reports

HTML reports are generated at:

- `tests/report.html`

The report includes the active Arduino sketch profile in the Environment section.

By default, runner scripts remove any previous `report.html` before starting a new run.

## Cleanup

Remove generated files from `tests/`:

```bash
./tests/clean.sh
```

```bat
tests\clean.bat
```

This removes build folders, caches, virtual environments, logs, and the HTML report.

## Notes

- This project favors simple and explicit test runners over heavy abstraction.
- Wi-Fi credentials are intended to come from environment variables or local dotenv files, not from committed source files.
- The library itself stays intentionally minimal; environment-dependent behavior is tested in dedicated sketches under `tests/`.
