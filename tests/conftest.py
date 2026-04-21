import os
import subprocess
from pathlib import Path
import tomllib

import pytest
from pytest_metadata.plugin import metadata_key

TESTS_DIR = Path(__file__).parent
DOTENV_FILES = (TESTS_DIR / ".env", TESTS_DIR / ".env.local")


# Register the small set of project-level CLI options we support.
def pytest_addoption(parser):
    parser.addoption(
        "--run-mode",
        action="store",
        choices=("all", "build", "test"),
        default="all",
        help="Select whether to run build only, tests only, or both.",
    )
    parser.addoption(
        "--profile",
        action="store",
        help="Arduino CLI sketch profile name passed to `arduino-cli compile -m`.",
    )
    parser.addoption(
        "--upload-mode",
        action="store",
        choices=("embedded", "arduino-cli"),
        default="embedded",
        help=(
            "Select how test runs upload firmware: "
            "'embedded' uses pytest-embedded auto flash with erase-all for clean runs, "
            "but only supports standard board definitions where the third FQBN field is the chip target; "
            "'arduino-cli' uses `arduino-cli upload` for wider board support, "
            "but preserves existing flash contents such as NVS and SPIFFS."
        ),
    )


# Load simple KEY=VALUE pairs from local dotenv files under tests/.
def load_dotenv_values():
    values = {}

    for path in DOTENV_FILES:
        if not path.is_file():
            continue

        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue

            if value and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]

            values[key] = value

    return values


DOTENV_VALUES = load_dotenv_values()
# Use local dotenv files as defaults without overriding real environment variables.
for key, value in DOTENV_VALUES.items():
    os.environ.setdefault(key, value)


# Read the optional Arduino sketch profile selected for this pytest run.
def get_profile_name(config):
    return config.getoption("--profile")


# Read the selected firmware upload strategy for this pytest run.
def get_upload_mode(config):
    return config.getoption("--upload-mode")


# Check whether uploads should be delegated to arduino-cli.
def is_arduino_cli_upload_mode(config):
    return get_upload_mode(config).startswith("arduino-cli")


# Convert the active profile name into a profile-specific serial port env var.
def get_profile_port_env_name(config):
    profile = get_profile_name(config)
    if not profile:
        return None

    normalized = profile.upper().replace("-", "_")
    return f"TEST_SERIAL_PORT_{normalized}"


# Map each test app to a profile-specific build output directory.
def get_build_dir(config, app_path):
    profile = get_profile_name(config)
    build_root = Path(app_path) / "build"
    if profile:
        return str(build_root / profile)

    return str(build_root / "default")


# Load test-app-specific define mappings when present.
def load_build_config(app_path):
    config_path = Path(app_path) / "build_config.toml"
    if not config_path.is_file():
        return {}

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    defines = data.get("defines", {})
    if not isinstance(defines, dict):
        raise ValueError(f"'defines' in {config_path} must be a table")

    return defines


# Quote define values safely for arduino-cli build properties.
def format_define_value(value):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


# Convert configured environment values into arduino-cli build properties.
def get_build_properties(config, app_path):
    defines = load_build_config(app_path)
    extra_flags = []

    for setting_name, define_name in defines.items():
        # Forward selected environment values into the sketch as compile-time defines.
        value = os.getenv(setting_name)
        if value is None:
            continue

        extra_flags.append(f"-D{define_name}={format_define_value(value)}")

    if not extra_flags:
        return []

    return [
        "--build-property",
        f"build.extra_flags={' '.join(extra_flags)}",
    ]


# Resolve the upload port using flashing-specific settings first.
def get_upload_port(config):
    flash_port = config.getoption("--flash-port")
    if flash_port:
        return flash_port

    return config.getoption("--port")


# Apply project-specific defaults before pytest starts collecting tests.
def pytest_configure(config):
    profile = get_profile_name(config) or "default"
    env_name = get_profile_port_env_name(config)
    if not config.getoption("--port"):
        port = os.getenv(env_name) if env_name else None
        if not port:
            port = os.getenv("TEST_SERIAL_PORT")
        if port:
            config.option.port = port

    config.stash[metadata_key]["Profile"] = profile
    config.stash[metadata_key]["Upload Mode"] = get_upload_mode(config)


# Show the active profile in the pytest session header.
def pytest_report_header(config):
    return [
        f"profile: {get_profile_name(config) or 'default'}",
        f"upload-mode: {get_upload_mode(config)}",
    ]


@pytest.fixture
# Expose the build directory to pytest-embedded.
def build_dir(request):
    return get_build_dir(request.config, Path(request.fspath).parent)


@pytest.fixture(scope="module", autouse=True)
# Build each sketch automatically unless the run is test-only.
def arduino_cli_build(request):
    config = request.config
    run_mode = request.config.getoption("--run-mode")
    if run_mode == "test":
        return

    # Keep build outputs separated by test app and selected profile.
    app_path = Path(request.fspath).parent
    build_dir = get_build_dir(config, app_path)
    command = [
        "arduino-cli",
        "compile",
        "--build-path",
        build_dir,
    ]

    profile = get_profile_name(config)
    if profile:
        command.extend(["-m", profile])

    command.extend(get_build_properties(config, app_path))

    subprocess.run(command, cwd=app_path, check=True)


@pytest.fixture
# Disable pytest-embedded autoflash when arduino-cli handles uploads.
def skip_autoflash(request):
    if is_arduino_cli_upload_mode(request.config):
        return True

    return request.config.getoption("--skip-autoflash")


@pytest.fixture(scope="module", autouse=True)
# Upload each sketch with arduino-cli when that upload mode is active.
def arduino_cli_upload(request, arduino_cli_build):
    config = request.config
    if config.getoption("--run-mode") == "build" or not is_arduino_cli_upload_mode(config):
        return

    app_path = Path(request.fspath).parent
    build_dir = Path(get_build_dir(config, app_path))
    if not build_dir.is_dir():
        raise FileNotFoundError(
            f"build output directory not found: {build_dir}. "
            "Run with --run-mode=all first, or build the sketch before test-only runs."
        )

    command = [
        "arduino-cli",
        "upload",
        "--build-path",
        str(build_dir),
    ]

    profile = get_profile_name(config)
    if profile:
        command.extend(["-m", profile])

    port = get_upload_port(config)
    if port:
        command.extend(["-p", port])

    command.append(str(app_path))

    subprocess.run(command, cwd=app_path, check=True)


@pytest.fixture(autouse=True)
# Skip Python-side DUT execution when running in build-only mode.
def skip_test_execution_in_build_mode(request, arduino_cli_build):
    if request.config.getoption("--run-mode") == "build":
        pytest.skip("skipped test execution in build-only mode")
