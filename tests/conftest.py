import os
import subprocess
from pathlib import Path
import tomllib
import pytest

TESTS_DIR = Path(__file__).parent
DOTENV_FILES = (TESTS_DIR / ".env", TESTS_DIR / ".env.local")


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


def get_profile_name(config):
    return config.getoption("--profile")


def get_build_dir(config, app_path):
    profile = get_profile_name(config)
    build_root = Path(app_path) / "build"
    if profile:
        return str(build_root / profile)

    return str(build_root / "default")


def get_first_env(*names):
    for name in names:
        value = os.getenv(name)
        if value:
            return value

        dotenv_value = DOTENV_VALUES.get(name)
        if dotenv_value:
            return dotenv_value

    return None


def resolve_option_or_env(config, option_name, *env_names):
    option_value = config.getoption(option_name)
    if option_value:
        return option_value

    return get_first_env(*env_names)


def get_resolved_settings(config):
    return {
        "TEST_SERIAL_PORT": resolve_option_or_env(config, "port", "TEST_SERIAL_PORT", "ESPPORT"),
        "TEST_WIFI_SSID": resolve_option_or_env(config, "wifi_ssid", "TEST_WIFI_SSID"),
        "TEST_WIFI_PASSWORD": resolve_option_or_env(config, "wifi_password", "TEST_WIFI_PASSWORD"),
    }


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


def format_define_value(value):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def get_build_properties(config, app_path):
    resolved_settings = get_resolved_settings(config)
    defines = load_build_config(app_path)
    extra_flags = []

    for setting_name, define_name in defines.items():
        value = resolved_settings.get(setting_name)
        if value is None:
            continue

        extra_flags.append(f"-D{define_name}={format_define_value(value)}")

    if not extra_flags:
        return []

    return [
        "--build-property",
        f"build.extra_flags={' '.join(extra_flags)}",
    ]


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
        "--wifi-ssid",
        action="store",
        help="Wi-Fi SSID for environment-dependent tests.",
    )
    parser.addoption(
        "--wifi-password",
        action="store",
        help="Wi-Fi password for environment-dependent tests.",
    )


def pytest_configure(config):
    resolved_settings = get_resolved_settings(config)

    resolved_port = resolved_settings["TEST_SERIAL_PORT"]
    if resolved_port and not config.getoption("port"):
        config.option.port = resolved_port

    resolved_wifi_ssid = resolved_settings["TEST_WIFI_SSID"]
    if resolved_wifi_ssid and not config.getoption("wifi_ssid"):
        config.option.wifi_ssid = resolved_wifi_ssid

    resolved_wifi_password = resolved_settings["TEST_WIFI_PASSWORD"]
    if resolved_wifi_password and not config.getoption("wifi_password"):
        config.option.wifi_password = resolved_wifi_password


def pytest_report_header(config):
    profile = get_profile_name(config) or "default"
    resolved_settings = get_resolved_settings(config)
    header = [
        f"profile: {profile}",
        f"build_dir_name: {profile}",
    ]

    resolved_port = resolved_settings["TEST_SERIAL_PORT"]
    if resolved_port:
        header.append(f"port: {resolved_port}")

    resolved_wifi_ssid = resolved_settings["TEST_WIFI_SSID"]
    if resolved_wifi_ssid:
        header.append(f"wifi_ssid: {resolved_wifi_ssid}")

    return header


@pytest.fixture
def build_dir(request):
    return get_build_dir(request.config, Path(request.fspath).parent)


@pytest.fixture
def wifi_ssid(request):
    return resolve_option_or_env(request.config, "wifi_ssid", "TEST_WIFI_SSID")


@pytest.fixture
def wifi_password(request):
    return resolve_option_or_env(request.config, "wifi_password", "TEST_WIFI_PASSWORD")


@pytest.fixture(scope="module", autouse=True)
def build(request):
    config = request.config
    run_mode = request.config.getoption("--run-mode")
    if run_mode == "test":
        return

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


@pytest.fixture(autouse=True)
def skip_test_execution_in_build_mode(request, build):
    if request.config.getoption("--run-mode") == "build":
        pytest.skip("skipped test execution in build-only mode")
